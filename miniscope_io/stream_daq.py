"""
DAQ For use with FPGA and Uart streaming video sources.
"""

import argparse
import multiprocessing
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Generator, List, Literal, Optional, Tuple, Union

import cv2
import numpy as np
import serial
from bitstring import Array, BitArray, Bits

from miniscope_io import init_logger
from miniscope_io.devices.mocks import okDevMock
from miniscope_io.exceptions import EndOfRecordingException, StreamReadError
from miniscope_io.formats.stream import StreamBufferHeader
from miniscope_io.models.buffer import BufferHeader
from miniscope_io.models.stream import StreamBufferHeaderFormat, StreamDaqConfig

HAVE_OK = False
ok_error = None
try:
    from miniscope_io.devices.opalkelly import okDev

    HAVE_OK = True
except (ImportError, ModuleNotFoundError):
    module_logger = init_logger("streamDaq")
    module_logger.warning(
        "Could not import OpalKelly driver, you can't read from FPGA!\n"
        "Check out Opal Kelly's website for install info\n"
        "https://docs.opalkelly.com/fpsdk/getting-started/"
    )

# Parsers for daq inputs
daqParser = argparse.ArgumentParser("streamDaq")
daqParser.add_argument("-c", "--config", help="YAML config file path: string")


def exact_iter(f: Callable, sentinel: Any) -> Generator[Any, None, None]:
    """
    A version of :func:`iter` that compares with `is` rather than `==`
    because truth value of numpy arrays is ambiguous.
    """
    while True:
        val = f()
        if val is sentinel:
            break
        else:
            yield val


class StreamDaq:
    """
    A combined class for configuring and reading frames from a UART and FPGA source.
    Supported devices and required inputs are described in StreamDaqConfig model documentation.
    This function's entry point is the main function, which should be used from the
    stream_image_capture command installed with the package.
    Example configuration yaml files are stored in /miniscope-io/config/.

    Examples
    --------
    >>> streamDaq -c path/to/config/yaml/file.yml
    Connected to XEM7310-A75
    Succesfully uploaded /miniscope-io/miniscope_io/devices/selected_bitfile.bit
    FrontPanel is supported

    .. todo::

        Example section: add the terminal output when running the script
        Phil/Takuya - docstrings for stream daq: what devices these correspond to,
        how to configure them, usage examples, tests

    """

    def __init__(
        self,
        config: StreamDaqConfig,
        header_fmt: StreamBufferHeaderFormat = StreamBufferHeader,
    ) -> None:
        """
        Constructer for the class.
        This parses configuration from the input yaml file.

        Parameters
        ----------
        config : StreamDaqConfig
            DAQ configurations imported from the input yaml file.
            Examples and required properties can be found in /miniscope-io/config/example.yml
        header_fmt : MetadataHeaderFormat, optional
            Header format used to parse information from buffer header,
            by default `MetadataHeaderFormat()`.
        """
        self.logger = init_logger("streamDaq")
        self.config = config
        self.header_fmt = header_fmt
        self.preamble = self.config.preamble
        self._buffer_npix: Optional[List[int]] = None
        self._nbuffer_per_fm: Optional[int] = None
        self.terminate: multiprocessing.Event = multiprocessing.Event()

    @property
    def buffer_npix(self) -> List[int]:
        """List of pixels per buffer for a frame"""
        if self._buffer_npix is None:
            px_per_frame = self.config.frame_width * self.config.frame_height
            px_per_buffer = (
                self.config.buffer_block_length * self.config.block_size
                - self.config.header_len / 8
            )
            quotient, remainder = divmod(px_per_frame, px_per_buffer)
            self._buffer_npix = [int(px_per_buffer)] * int(quotient) + [int(remainder)]
        return self._buffer_npix

    @property
    def nbuffer_per_fm(self) -> int:
        """
        Number of buffers per frame, computed from :attr:`.buffer_npix`
        """
        if self._nbuffer_per_fm is None:
            self._nbuffer_per_fm = len(self.buffer_npix)
        return self._nbuffer_per_fm

    def _parse_header(
        self, buffer: Bits, truncate: Literal["preamble", "header", False] = False
    ) -> Tuple[BufferHeader, bytes]:
        """
        Function to parse header from each buffer.

        Parameters
        ----------
        buffer : bytes
            Input buffer.
        truncate : Literal[preamble, header, False], optional
            Whether the parsed header should be truncated from the returned buffer.
            If `"preamble"`, then only the preamble is truncated.
            If `"header"`, then the full header is truncated.
            If `False`, then `buffer` is returned untouched.

        Returns
        -------
        Tuple[BufferHeader, bytes]
            The returned header data and (optionally truncated) buffer data.
        """
        pre = Bits(self.preamble)
        if self.config.LSB:
            pre = pre[::-1]
        pre_len = len(pre)
        assert buffer[:pre_len] == pre
        header_data = dict()
        for hd, bit_range in self.header_fmt.model_dump().items():
            b = buffer[pre_len + bit_range[0] : pre_len + bit_range[1]]
            if self.config.LSB:
                header_data[hd] = b[::-1].uint
            else:
                header_data[hd] = b.uint

        header_data = BufferHeader.model_construct(**header_data)

        if truncate == "preamble":
            return header_data, buffer[pre_len:]
        elif truncate == "header":
            return header_data, buffer[self.config.header_len :]
        else:
            return header_data, buffer

    def _uart_recv(
        self, serial_buffer_queue: multiprocessing.Queue, comport: str, baudrate: int
    ) -> None:
        """
        Receive buffers and push into serial_buffer_queue.
        Currently not supported.

        Parameters
        ----------
        serial_buffer_queue : multiprocessing.Queue
            _description_
        comport : str
            _description_
        baudrate : int
            _description_
        """
        pre_bytes = bytes(bytearray(self.preamble.tobytes())[::-1])

        # set up serial port
        serial_port = serial.Serial(port=comport, baudrate=baudrate, timeout=5, stopbits=1)
        self.logger.info("Serial port open: " + str(serial_port.name))

        # Throw away the first buffer because it won't fully come in
        uart_bites = serial_port.read_until(pre_bytes)
        log_uart_buffer = BitArray([x for x in uart_bites])

        try:
            while 1:
                # read UART data until preamble and put into queue
                uart_bites = serial_port.read_until(pre_bytes)
                log_uart_buffer = [x for x in uart_bites]
                serial_buffer_queue.put(log_uart_buffer)
        finally:
            time.sleep(1)  # time for ending other process
            serial_port.close()
            self.logger.info("Close serial port")
            sys.exit(1)

    def _init_okdev(self, BIT_FILE: Path) -> Union[okDev, okDevMock]:

        # FIXME: when multiprocessing bug resolved, remove this and just mock in tests
        dev = okDevMock() if os.environ.get("PYTEST_CURRENT_TEST") is not None else okDev()

        dev.uploadBit(str(BIT_FILE))
        dev.setWire(0x00, 0b0010)
        time.sleep(0.01)
        dev.setWire(0x00, 0b0)
        dev.setWire(0x00, 0b1000)
        time.sleep(0.01)
        dev.setWire(0x00, 0b0)
        return dev

    def _fpga_recv(
        self,
        serial_buffer_queue: multiprocessing.Queue,
        read_length: int = None,
        pre_first: bool = True,
        capture_binary: Optional[Path] = None,
    ) -> None:
        """
        Function to read bitstream from OpalKelly device and store buffer in `serial_buffer_queue`.

        The bits data are read in fixed chunks defined by `read_length`.
        Then we concatenate the chunks and try to look for `self.preamble` in the data.
        The data between every pair of `self.preamble` is considered to be a single buffer and
        stored in `serial_buffer_queue`.

        Parameters
        ----------
        serial_buffer_queue : multiprocessing.Queue[bytes]
            The queue holding the buffer data.
        read_length : int, optional
            Length of data to read in chunks (in number of bytes), by default None.
            If `None`, an optimal length is estimated so that it roughly covers a single buffer
            and is an integer multiple of 16 bytes (as recommended by OpalKelly).
        pre_first : bool, optional
            Whether preamble/header is returned at the beginning of each buffer, by default True.
        capture_binary: Path, optional
            save binary directly from the ``okDev`` to the supplied path, if present.

        Raises
        ------
        RuntimeError
            If the OpalKelly device library cannot be found
        """
        if not HAVE_OK:
            raise RuntimeError(
                "Couldnt import OpalKelly device. Check the docs for install instructions!"
            )
        # determine length
        if read_length is None:
            read_length = int(max(self.buffer_npix) * self.config.pix_depth / 8 / 16) * 16

        # set up fpga devices
        BIT_FILE = self.config.bitstream
        if not BIT_FILE.exists():
            raise RuntimeError(f"Configured to use bitfile at {BIT_FILE} but no such file exists")
        # set up fpga devices

        dev = self._init_okdev(BIT_FILE)

        # read loop
        cur_buffer = BitArray()
        pre = Bits(self.preamble)
        if self.config.LSB:
            pre = pre[::-1]

        while not self.terminate.is_set():
            try:
                buf = dev.readData(read_length)
            except (EndOfRecordingException, StreamReadError, KeyboardInterrupt):
                self.terminate.set()
                serial_buffer_queue.put(None)
                break

            if capture_binary:
                with open(capture_binary, "ab") as file:
                    file.write(buf)

            dat = BitArray(buf)
            cur_buffer = cur_buffer + dat
            pre_pos = list(cur_buffer.findall(pre))
            for buf_start, buf_stop in zip(pre_pos[:-1], pre_pos[1:]):
                if not pre_first:
                    buf_start, buf_stop = buf_start + len(self.preamble), buf_stop + len(
                        self.preamble
                    )
                serial_buffer_queue.put(cur_buffer[buf_start:buf_stop].tobytes())
            if pre_pos:
                cur_buffer = cur_buffer[pre_pos[-1] :]

    def _buffer_to_frame(
        self,
        serial_buffer_queue: multiprocessing.Queue,
        frame_buffer_queue: multiprocessing.Queue,
    ) -> None:
        """
        Group buffers together to make frames.

        Pull out buffers in `serial_buffer_queue`, then get frame and buffer index by
        parsing headers in the buffer.
        The buffers belonging to the same frame are put in the same list at
        corresponding buffer index.
        The lists representing each frame are then put into `frame_buffer_queue`.

        Parameters
        ----------
        serial_buffer_queue : multiprocessing.Queue[bytes]
            Input buffer queue.
        frame_buffer_queue : multiprocessing.Queue[list[bytes]]
            Output frame queue.
        """
        locallogs = init_logger("streamDaq.buffer")

        cur_fm_buffer_index = -1  # Index of buffer within frame
        cur_fm_num = -1  # Frame number

        frame_buffer = [None] * self.nbuffer_per_fm

        try:
            for serial_buffer in exact_iter(serial_buffer_queue.get, None):
                serial_buffer = Bits(serial_buffer)

                header_data, serial_buffer = self._parse_header(serial_buffer)

                # log metadata
                locallogs.debug(str(header_data.model_dump()))

                # if first buffer of a frame
                if header_data.frame_num != cur_fm_num:
                    # discard first incomplete frame
                    if cur_fm_num == -1 and header_data.frame_buffer_count != 0:
                        continue

                    # push frame_buffer into frame_buffer queue
                    frame_buffer_queue.put(frame_buffer)
                    # init frame_buffer
                    frame_buffer = [None] * self.nbuffer_per_fm

                    # update frame_num and index
                    cur_fm_num = header_data.frame_num
                    cur_fm_buffer_index = header_data.frame_buffer_count

                    # update data
                    frame_buffer[cur_fm_buffer_index] = serial_buffer.tobytes()

                    if cur_fm_buffer_index != 0:
                        locallogs.warning(
                            f"Frame {cur_fm_num} started with buffer {cur_fm_buffer_index}"
                        )

                # if same frame_num with previous buffer.
                elif (
                    header_data.frame_num == cur_fm_num
                    and header_data.frame_buffer_count > cur_fm_buffer_index
                ):
                    cur_fm_buffer_index = header_data.frame_buffer_count
                    frame_buffer[cur_fm_buffer_index] = serial_buffer.tobytes()
                    locallogs.debug("----buffer #" + str(cur_fm_buffer_index) + " stored")

                # if lost frame from buffer -> reset index
                else:
                    cur_fm_buffer_index = 0
        finally:
            frame_buffer_queue.put(None)

    def _format_frame(
        self,
        frame_buffer_queue: multiprocessing.Queue,
        imagearray: multiprocessing.Queue,
    ) -> None:
        """
        Construct frame from grouped buffers.

        Each frame data is concatenated from a list of buffers in `frame_buffer_queue`
        according to `buffer_npix`.
        If there is any mismatch between the expected length of each buffer
        (defined by `buffer_npix`) and the actual length, then the buffer is either
        truncated or zero-padded at the end to make the length appropriate,
        and a warning is thrown.
        Finally, the concatenated buffer data are converted into a 1d numpy array with
        uint8 dtype and put into `imagearray` queue.

        Parameters
        ----------
        frame_buffer_queue : multiprocessing.Queue[list[bytes]]
            Input buffer queue.
        imagearray : multiprocessing.Queue[np.ndarray]
            Output image array queue.
        """
        locallogs = init_logger("streamDaq.frame")
        header_data = None
        try:
            for frame_data in exact_iter(frame_buffer_queue.get, None):
                locallogs.debug("Found frame in queue")

                nbit_lost = 0

                for i, npix_expected in enumerate(self.buffer_npix):
                    if frame_data[i] is not None:
                        header_data, fm_dat = self._parse_header(
                            Bits(frame_data[i]), truncate="header"
                        )
                    else:
                        frame_data[i] = Bits(int=0, length=npix_expected * self.config.pix_depth)
                        nbit_lost += npix_expected
                        continue
                    npix_header = header_data.pixel_count
                    npix_actual = len(fm_dat) / self.config.pix_depth

                    if npix_actual != npix_expected:
                        if i < len(self.buffer_npix) - 1:
                            locallogs.warning(
                                f"Pixel count inconsistent for frame {header_data.frame_num} "
                                f"buffer {header_data.frame_buffer_count}. "
                                f"Expected: {npix_expected}, "
                                f"Header: {npix_header}, "
                                f"Actual: {npix_actual}"
                            )
                        nbit_expected = npix_expected * self.config.pix_depth
                        if len(fm_dat) > nbit_expected:
                            fm_dat = fm_dat[:nbit_expected]
                        else:
                            nbit_pad = nbit_expected - len(fm_dat)
                            fm_dat = fm_dat + Bits(int=0, length=nbit_pad)
                            nbit_lost += nbit_pad

                    frame_data[i] = fm_dat

                pixel_vector = frame_data[0]
                for d in frame_data[1:]:
                    pixel_vector = pixel_vector + d

                assert len(pixel_vector) == (
                    self.config.frame_height * self.config.frame_width * self.config.pix_depth
                )

                if self.config.LSB:
                    pixel_vector = Array(
                        "uint:32",
                        [
                            pixel_vector[i : i + 32][::-1].uint
                            for i in reversed(range(0, len(pixel_vector), 32))
                        ],
                    )
                img = np.frombuffer(pixel_vector.tobytes(), dtype=np.uint8)
                imagearray.put(img)

                if header_data is not None:
                    locallogs.info(f"frame: {header_data.frame_num}, bits lost: {nbit_lost}")
        finally:
            imagearray.put(None)

    def init_video(self, path: Path, fourcc: str = "Y800", **kwargs: dict) -> cv2.VideoWriter:
        """
        Create a parameterized video writer

        Args:
            path (:class:`pathlib.Path`): Video file to write to
            fourcc (str): Fourcc code to use
            kwargs: passed to :class:`cv2.VideoWriter`

        Returns:
            :class:`cv2.VideoWriter`
        """
        fourcc = cv2.VideoWriter_fourcc(*fourcc)
        frame_rate = self.config.fs
        frame_size = (self.config.frame_width, self.config.frame_height)
        out = cv2.VideoWriter(str(path), fourcc, frame_rate, frame_size, **kwargs)
        return out

    def capture(
        self,
        source: Literal["uart", "fpga"],
        read_length: Optional[int] = None,
        video: Optional[Path] = None,
        video_kwargs: Optional[dict] = None,
        binary: Optional[Path] = None,
    ) -> None:
        """
        Entry point to start frame capture.

        Parameters
        ----------
        source : Literal[uart, fpga]
            Device source.
        read_length : Optional[int], optional
            Passed to :func:`~miniscope_io.stream_daq.stream_daq._fpga_recv` when
            `source == "fpga"`, by default None.
        video: Path, optional
            If present, a path to an output video file
        video_kwargs: dict, optional
            kwargs passed to :meth:`.init_video`
        binary: Path, optional
            Save raw binary directly from ``okDev`` to file, if present.
            Note that binary is captured in *append* mode, rather than rewriting an existing file.

        Raises
        ------
        ValueError
            If `source` is not in `("uart", "fpga")`.
        """
        self.terminate.clear()

        # Queue size is hard coded
        queue_manager = multiprocessing.Manager()
        serial_buffer_queue = queue_manager.Queue(
            10
        )  # b'\x00' # hand over single buffer: uart_recv() -> buffer_to_frame()
        frame_buffer_queue = queue_manager.Queue(5)  # [b'\x00', b'\x00', b'\x00', b'\x00', b'\x00']
        # hand over a frame (five buffers): buffer_to_frame()
        imagearray = queue_manager.Queue(5)
        imagearray.put(np.zeros(int(self.config.frame_width * self.config.frame_height), np.uint8))

        if source == "uart":
            self.logger.debug("Starting uart capture process")
            p_recv = multiprocessing.Process(
                target=self._uart_recv,
                args=(
                    serial_buffer_queue,
                    self.config["port"],
                    self.config["baudrate"],
                ),
            )
        elif source == "fpga":
            self.logger.debug("Starting fpga capture process")
            p_recv = multiprocessing.Process(
                target=self._fpga_recv,
                args=(serial_buffer_queue, read_length, True, binary),
            )
        else:
            raise ValueError(f"source can be one of uart or fpga. Got {source}")

        # Video output
        if video:
            if video_kwargs is None:
                video_kwargs = {}

            writer = self.init_video(video, **video_kwargs)
        else:
            writer = None

        p_buffer_to_frame = multiprocessing.Process(
            target=self._buffer_to_frame,
            args=(
                serial_buffer_queue,
                frame_buffer_queue,
            ),
        )
        p_format_frame = multiprocessing.Process(
            target=self._format_frame,
            args=(
                frame_buffer_queue,
                imagearray,
            ),
        )
        """
        p_terminate = multiprocessing.Process(
            target=check_termination_flag, args=(self.terminate,))
        """
        p_recv.start()
        p_buffer_to_frame.start()
        p_format_frame.start()
        # p_terminate.start()
        try:
            for imagearray_plot in exact_iter(imagearray.get, None):
                image = imagearray_plot.reshape(self.config.frame_width, self.config.frame_height)
                if self.config.show_video is True:
                    cv2.imshow("image", image)
                if writer:
                    picture = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)  # If your image is grayscale
                    writer.write(picture)
        except KeyboardInterrupt:
            self.terminate.set()
        finally:
            if writer:
                writer.release()
                self.logger.debug("VideoWriter released")
            if self.config.show_video:
                cv2.destroyAllWindows()

            self.logger.debug("End capture")


def main() -> None:  # noqa: D103
    args = daqParser.parse_args()

    daqConfig = StreamDaqConfig.from_yaml(args.config)

    daq_inst = StreamDaq(config=daqConfig)

    if daqConfig.device == "UART":
        daq_inst.capture(source="uart")

    if daqConfig.device == "OK":
        if not HAVE_OK:
            raise ImportError(
                f"Requested Opal Kelly DAQ, but okDAQ could not be imported, got exception: "
                f"{ok_error}"
            )

        daq_inst.capture(source="fpga")


if __name__ == "__main__":
    main()
