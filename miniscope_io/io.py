"""
I/O functions for the SD card
"""
from typing import Union, BinaryIO
from pathlib import Path
import warnings

import numpy as np

from miniscope_io.sdcard import SDLayout, SDConfig, DataHeader
from miniscope_io.exceptions import InvalidSDException



class SDCard:
    """
    I/O for data on an SDCard

    an instance of :class:`.sdcard.SDLayout` (typically in :mod:`.formats` ) configures how
    the data is laid out on the SD card. This class makes the i/o operations abstract over
    multiple layouts
    """

    def __init__(
            self,
            drive: Union[str, Path],
            layout: SDLayout

        ):
        """

        Args:
            drive (str, :class:`pathlib.Path`): Path to the SD card drive
            layout (:class:`.sdcard.SDLayout`): A layout configuration for an SD card
        """
        self.drive = Path(drive).resolve()
        self.layout = layout

        self._config = None

        if not self.check_valid():
            raise InvalidSDException(f"The SD card at path {str(self.drive)} does not have the correct WRITEKEYs in its header!")

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def config(self) -> SDConfig:
        if self._config is None:
            with open(self.drive, 'rb') as sd:
                sd.seek(self.layout.config_pos, 0)
                configSectorData = np.frombuffer(sd.read(self.layout.sectors.size), dtype=np.uint32)
            self._config = SDConfig(
                width  = configSectorData[self.layout.config.width],
                height = configSectorData[self.layout.config.height],
                fs     = configSectorData[self.layout.config.fs],
                buffer_size = configSectorData[self.layout.config.buffer_size],
                n_buffers_recorded =configSectorData[self.layout.config.n_buffers_recorded],
                n_buffers_dropped=configSectorData[self.layout.config.n_buffers_dropped]
            )

        return self._config

    # --------------------------------------------------
    # read methods
    # --------------------------------------------------
    def _read_data_header(self, sd:BinaryIO) -> DataHeader:
        """
        Given an already open file buffer opened in bytes mode,
         seeked to the start of a frame, read the data header
        """

        # read one word first, I think to get the size of the rest of the header,
        # that sort of breaks the abstraction (it assumes the buffer length is always at position 0)
        # but we'll roll with it for now
        dataHeader = np.frombuffer(sd.read(self.layout.word_size), dtype=np.uint32)
        dataHeader = np.append(
            dataHeader,
            np.frombuffer(
                sd.read((dataHeader[self.layout.buffer.length] - 1) * self.layout.word_size),
                dtype=np.uint32
            )
        )
        # use construct because we're already sure these are ints from the numpy casting
        #https://docs.pydantic.dev/latest/usage/models/#creating-models-without-validation
        header = DataHeader.construct(
            length = dataHeader[self.layout.buffer.length],
            linked_list = dataHeader[self.layout.buffer.linked_list],
            frame_num= dataHeader[self.layout.buffer.frame_num],
            buffer_count= dataHeader[self.layout.buffer.buffer_count],
            frame_buffer_count= dataHeader[self.layout.buffer.frame_buffer_count],
            write_buffer_count= dataHeader[self.layout.buffer.write_buffer_count],
            dropped_buffer_count= dataHeader[self.layout.buffer.dropped_buffer_count],
            timestamp= dataHeader[self.layout.buffer.timestamp],
            data_length= dataHeader[self.layout.buffer.data_length],
        )
        return header

    def _read_buffer(self, sd: BinaryIO, header: DataHeader) -> np.ndarray:
        """
        Read a single buffer from a frame.

        Each frame has several buffers, so for a given frame we read them until we get another that's zero!
        """
        # not sure whats goin on here!
        numBlocks = int(
            (
                    header.data_length +
                    (header.length * self.layout.word_size) +
                    (self.layout.sectors.size - 1)
            ) / self.layout.sectors.size
        )
        data = np.frombuffer(
            sd.read(numBlocks * 512 - header.length * 4),
            dtype=np.uint8
        )
        return data

    def reader(self):
        """
        Python generator that yields the next frame.

        Examples:

            # sd = SDCard(...)
            reader = sd.reader()
            frame = next(reader)

            # or
            for frame in sd.reader():
                # do something...

        """
        with open(self.drive, 'rb') as sd:
            # seek to the right position
            sd.seek(self.layout.sectors.data_pos, 0)

            # create an empty frame to hold our data!
            frame = np.zeros(
                (self.config.width * self.config.height, 1),
                dtype=np.uint8
            )
            pixel_count = 0
            last_buffer_n = 0

            # iterate until we run out of data!
            while True:
                # read header and then buffers
                # since each read operation advances the seek, each of these are private methods
                # that should only be called here in order
                header = self._read_data_header(sd)

                # if we are back at the zeroth buffer and have already looped through a frame,
                # yield it before reading the next frame's buffer
                if header.frame_buffer_count == 0 and last_buffer_n > 0:
                    yield np.reshape(
                        frame,
                       (self.config.width, self.config.height)
                    )
                    # TODO: Check if we're copying or returning a view above, if we're returning a view then we need to make a new array
                    frame[:] = 0
                    pixel_count = 0

                data = self._read_buffer(sd, header)
                if data is None:
                    # at the end of the file!
                    break

                # warn if we didn't get the expected size of data
                if data.shape[0] != header.data_length:
                    warnings.warn(f"Expected buffer data length: {header.data_length}, got data with shape {data.shape}")

                # Put buffer data into the frame
                # we use the actual data length rather than the expected length of the data to index
                # so we may overrun the array and throw an error! the warning should let us know
                # that something is wrong with how we're grabbing frames or how they're shaped
                # so we know the problem is before here if the grabbed frame looks weird, but
                # throwing the exception will be an even stronger reminder to handle inconsistencies in length
                frame[pixel_count:pixel_count + data.shape[0], 0] = data
                last_buffer_n = header.frame_buffer_count
                pixel_count += data.shape[0]


    # --------------------------------------------------
    # General Methods
    # --------------------------------------------------

    def check_valid(self) -> bool:
        """
        Checks that the header sector has the appropriate write keys in it

        Returns:
            bool - True if valid, False if not
        """
        with open(self.drive, 'rb') as sd:
            sd.seek(self.layout.sectors.header_pos, 0)
            headerSectorData = np.frombuffer(sd.read(self.layout.sectors.size), dtype=np.uint32)

            valid = False
            if headerSectorData[0] == self.layout.write_key0 and \
                    headerSectorData[1] == self.layout.write_key1 and \
                    headerSectorData[2] == self.layout.write_key2 and \
                    headerSectorData[3] == self.layout.write_key3:
                valid = True

        return valid
