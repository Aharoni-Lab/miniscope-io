"""
I/O functions for the SD card
"""
from typing import Union, BinaryIO, Optional, Tuple, List
from pathlib import Path
import warnings

import numpy as np

from miniscope_io.sdcard import SDLayout, SDConfig, DataHeader
from miniscope_io.exceptions import InvalidSDException, EndOfRecordingException



class SDCard:
    """
    I/O for data on an SDCard

    an instance of :class:`.sdcard.SDLayout` (typically in :mod:`.formats` ) configures how
    the data is laid out on the SD card. This class makes the i/o operations abstract over
    multiple layouts

    Args:
        drive (str, :class:`pathlib.Path`): Path to the SD card drive
        layout (:class:`.sdcard.SDLayout`): A layout configuration for an SD card

    """

    def __init__(
            self,
            drive: Union[str, Path],
            layout: SDLayout

        ):

        self.drive = Path(drive).resolve()
        self.layout = layout

        # Private attributes used when the file reading context is entered
        self._config = None  # type: Optional[SDConfig]
        self._f = None  # type: Optional[BinaryIO]
        self._frame = None  # type: Optional[int]
        self._frame_count = None # type: Optional[int]
        self._array = None  # type: Optional[np.ndarray]
        """
        n_pix x 1 array used to store pixels while reading buffers
        """
        self.positions = {}
        """
        A mapping between frame number and byte position in the video that makes for faster seeking :)
        
        As we read, we store the locations of each frame before reading it. Later, we can assign to
        `frame` to seek back to those positions. Assigning to `frame` works without caching position, but
        has to manually iterate through each frame.
        """



        # this doesn't seem to be true anymore? but the WRITE_KEYs are still in
        # both the firmware and reading code, just unused?
        #if not self.check_valid():
        #    raise InvalidSDException(f"The SD card at path {str(self.drive)} does not have the correct WRITEKEYs in its header!")

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def config(self) -> SDConfig:
        if self._config is None:
            with open(self.drive, 'rb') as sd:
                sd.seek(self.layout.sectors.config_pos, 0)
                configSectorData = np.frombuffer(sd.read(self.layout.sectors.size), dtype=np.uint32)

            self._config = SDConfig(
                **{
                    k: configSectorData[v]
                    for k, v in self.layout.config.dict().items()
                    if v is not None
                }
            )

        return self._config

    @property
    def position(self) -> Optional[int]:
        """
        When entered as context manager, the current position of the internal file descriptor
        """
        if self._f is None:
            return None

        return self._f.tell()


    @property
    def frame(self) -> Optional[int]:
        """
        When reading, the number of the frame that would be read if we were to call :meth:`.read`
        """
        if self._f is None:
            return None

        return self._frame

    @frame.setter
    def frame(self, frame:int):
        """
        Seek to a specific frame

        Arguments:
            frame (int): The frame to seek to!
        """
        if self._f is None:
            raise RuntimeError("Havent entered context manager yet! Cant change position without that!")

        if frame == self.frame:
            return

        if frame in self.positions.keys():
            self._f.seek(self.positions[frame], 0)
            self._frame = frame
            return
        else:
            # TODO find the nearest position we do have
            pass

        if frame < self.frame:
            # hard to go back, esp if we haven't already been here (we should have stashed the position)
            # just go to start of data and seek like normally (next case)
            self._f.seek(self.layout.sectors.data_pos, 0)
            self._frame = 0

        if frame > self.frame:
            for i in range(frame - self.frame):
                self.skip()

    @property
    def frame_count(self) -> int:
        """
        Total number of frames in recording.

        Inferred from :class:`~.sdcard.SDConfig.n_buffers_recorded` and
        reading a single frame to get the number of buffers per frame.
        """
        if self._frame_count is None:
            if self._f is None:
                with self as self_open:
                    frame, headers = self_open.read(return_header=True)

            else:
                # If we're already open, great, just return to the last frame
                last_frame = self.frame
                frame, headers = self.read(return_header=True)
                self.frame = last_frame

            self._frame_count = int(np.ceil(
                (self.config.n_buffers_recorded + self.config.n_buffers_dropped) / len(headers)
            ))

        # if we have since read more frames than should be there, we update the frame count with a warning
        max_pos = np.max(list(self.positions.keys()))
        if max_pos > self._frame_count:
            warnings.warn(f'Got more frames than indicated in card header, expected {self._frame_count} but got {max_pos}')
            self._frame_count = int(max_pos)

        return self._frame_count



    # --------------------------------------------------
    # Context Manager methods
    # --------------------------------------------------

    def __enter__(self) -> 'SDCard':
        if self._f is not None:
            raise RuntimeError("Cant enter context, and open the file twice!")

        # init private attrs
        # create an empty frame to hold our data!
        self._array = np.zeros(
            (self.config.width * self.config.height, 1),
            dtype=np.uint8
        )
        self._pixel_count = 0
        self._last_buffer_n = 0
        self._frame = 0

        self._f = open(self.drive, 'rb')
        # seek to the start of the data
        self._f.seek(self.layout.sectors.data_pos, 0)
        # store the 0th frame position
        self.positions[0] = self.layout.sectors.data_pos

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._f.close()
        self._f = None
        self._frame = 0

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
            **{
                k: dataHeader[v]
                for k, v in self.layout.buffer.dict().items()
                if v is not None
            })
        return header

    def _n_frame_blocks(self, header: DataHeader) -> int:
        """
        Compute the number of blocks for a given frame buffer

        Not sure how this works!
        """
        n_blocks = int(
            (
                header.data_length +
                (header.length * self.layout.word_size) +
                (self.layout.sectors.size - 1)
            ) / self.layout.sectors.size
        )
        return n_blocks

    def _read_size(self, header: DataHeader) -> int:
        """
        Compute the number of bytes to read for a given buffer

        Not sure how this works with :meth:`._n_frame_blocks`, but keeping
        them separate in case they are separable actions for now
        """
        n_blocks = self._n_frame_blocks(header)
        read_size = (n_blocks * self.layout.sectors.size) - \
            (header.length * self.layout.word_size)
        return read_size

    def _read_buffer(self, sd: BinaryIO, header: DataHeader) -> np.ndarray:
        """
        Read a single buffer from a frame.

        Each frame has several buffers, so for a given frame we read them until we get another that's zero!
        """
        data = np.frombuffer(
            sd.read(self._read_size(header)),
            dtype=np.uint8
        )
        return data

    def _trim(self, data:np.ndarray, expected_size:int) -> np.ndarray:
        """
        Trim or pad an array to match an expected size
        """
        if data.shape[0] != expected_size:
            warnings.warn(
                f"Expected buffer data length: {expected_size}, got data with shape {data.shape}. Padding to expected length")

            # trim if too long
            if data.shape[0] > expected_size:
                data = data[0:expected_size]
            # pad if too short
            else:
                data = np.pad(data, (0, expected_size - data.shape[0]))

        return data

    def read(self, return_header:bool=False) -> Union[np.ndarray, Tuple[np.ndarray, List[DataHeader]]]:
        """
        Read a single frame

        Arguments:
            return_header (bool): If `True`, return headers from individual buffers (default `False`)

        Return:
            :class:`numpy.ndarray` , or a tuple(ndarray, List[:class:`~.DataHeader`]) if `return_header` is `True`
        """
        if self._f is None:
            raise RuntimeError('File is not open! Try entering the reader context by using it like `with sdcard:`')

        self._array[:] = 0
        pixel_count = 0
        last_buffer_n = 0
        headers = []
        while True:
            # stash position before reading header
            last_position = self._f.tell()
            try:
                header = self._read_data_header(self._f)
            except ValueError as e:
                if 'read length must be non-negative' in str(e):
                    # end of file! Value error thrown because the dataHeader will be blank,
                    # and thus have a value of 0 for the header size, and we can't read 0 from the card.
                    self._f.seek(last_position, 0)
                    raise EndOfRecordingException("Reached the end of the video!")
                else:
                    raise e
            except IndexError as e:
                if 'index 0 is out of bounds for axis 0 with size 0' in str(e):
                    # end of file if we are reading from a disk image without any additional space on disk
                    raise EndOfRecordingException("Reached the end of the video!")
                else:
                    raise e

            if header.frame_buffer_count == 0 and last_buffer_n > 0:
                # we are in the next frame!
                # rewind to the beginning of the header, and return
                # the last_position is the start of the header for this frame
                self._f.seek(last_position, 0)
                self._frame += 1
                self.positions[self._frame] = last_position
                frame = np.reshape(self._array, (self.config.width, self.config.height))
                if return_header:
                    return frame, headers
                else:
                    return frame

            # grab buffer data and stash
            headers.append(header)
            data = self._read_buffer(self._f, header)
            data = self._trim(data, header.data_length)
            self._array[pixel_count:pixel_count + header.data_length, 0] = data
            pixel_count += header.data_length
            last_buffer_n = header.frame_buffer_count

    def skip(self):
        """
        Skip a frame

        Read the buffer headers to determine buffer sizes and just seek ahead
        """
        if self._f is None:
            raise RuntimeError('File is not open! Try entering the reader context by using it like `with sdcard:`')

        last_position = self._f.tell()
        header = self._read_data_header(self._f)

        if header.frame_buffer_count != 0:
            self._f.seek(last_position, 0)
            raise RuntimeError("Did not start at the first buffer of a frame! Something is wrong with the way seeking is working. Rewound to where we started")

        while True:
            # jump ahead according to the last header we read
            read_size = self._read_size(header)
            self._f.seek(read_size, 1)

            # stash position before reading next buffer header
            last_position = self._f.tell()
            header = self._read_data_header(self._f)

            # if the frame is over, return to the start of the buffer and break,
            # incrementing the current frame count
            if header.frame_buffer_count == 0:
                self._f.seek(last_position, 0)
                self._frame += 1
                self.positions[self.frame] = last_position
                break


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
