import argparse
import logging
import multiprocessing
import os
import sys
import time
import warnings
from datetime import datetime
from typing import Any, Literal, Optional, Tuple

import coloredlogs
import cv2
import numpy as np
import serial
from bitstring import Array, BitArray, Bits
from pydantic import BaseModel

# Parsers for daq inputs
daqParser = argparse.ArgumentParser("stream_image_capture")
daqParser.add_argument("source", help='Input source; ["UART", "OK"]')
daqParser.add_argument("--port", help="serial port: string")
daqParser.add_argument("--baudrate", help="baudrate: int")

# Parsers for update LED
updateDeviceParser = argparse.ArgumentParser("updateDevice")
updateDeviceParser.add_argument("port", help="serial port")
updateDeviceParser.add_argument("baudrate", help="baudrate")
updateDeviceParser.add_argument("module", help="module to update")
updateDeviceParser.add_argument("value", help="LED value")


class MetadataHeaderFormat(BaseModel):
    """
    Format model used to parse header at the beginning of every buffer.

    The model attributes are key-value pairs mapping the variable/information in the header to their corresponding position (in bits) in the header.

    .. todo::

        Jonny: This model basically duplicates :class:`~miniscope_io.sdcard.BufferHeaderPositions`
        except using start:end tuples rather than start indices with a word length. Refactor these
        so we can ensure a single set of header terms and models. Split out SD-card specific models
        from ones we might want to use generally across miniscopes. These models being separate from the
        other format models sort of sucks but will do for this PR.

    .. todo::

        Everyone: Is there a better format than having these index classes AND the container classes?
        eg. :class:`~miniscope_io.sdcard.BufferHeaderPositions` and :class:`~miniscope_io.sdcard.DataHeader`

    """

    linked_list: Tuple[int, int] = (0, 32)
    frame_num: Tuple[int, int] = (32, 64)
    buffer_count: Tuple[int, int] = (64, 96)
    frame_buffer_count: Tuple[int, int] = (96, 128)
    timestamp: Tuple[int, int] = (192, 224)
    pixel_count: Tuple[int, int] = (224, 256)


class MetadataHeader(BaseModel):
    """
    Container for FPGA header data, structured by :class:`.MetadataHeaderFormat`

    """

    linked_list: Any
    """
    Not sure what this is!
    """
    frame_num: int
    buffer_count: int
    frame_buffer_count: int
    timestamp: int
    pixel_count: int


class stream_daq:
    """
    A combined class for reading frames from a UART and FPGA source.

    .. todo::

        Phil/Takuya - docstrings for stream daq: what devices these correspond to, how to configure them, usage examples, tests

    """

    def __init__(
        self,
        frame_width: int = 304,
        frame_height: int = 304,
        preamble: bytes = b"\x12\x34\x56",
        header_fmt: MetadataHeaderFormat = MetadataHeaderFormat(),
        header_len: int = 11,
        LSB: bool = True,
        buffer_npix: Tuple[int] = (20432, 20432, 20432, 20432, 10688),
        pix_depth: int = 8,
    ) -> None:
        """
        Constructer for the class.

        Currently supports UART and FPGA source.

        Parameters
        ----------
        frame_width : int, optional
            Width of the frame (in pixels), by default 304.
        frame_height : int, optional
            Height of the frame (in pixels), by default 304.
        preamble : bytes, optional
            Preamble string at the beginning of every buffer header, by default b"\x12\x34\x56".
        header_fmt : MetadataHeaderFormat, optional
            Header format used to parse information from buffer header, by default `MetadataHeaderFormat()`.
        header_len : int, optional
            Length of header in (32-bit) words, by default 11.
            This is useful when not all the variable/words in the header are defined in :class:`.MetadataHeaderFormat`.
            The user is responsible to ensure that `header_len * 32` is larger than the largest bit position defined in :class:`.MetadataHeaderFormat` otherwise unexpected behavior might occur.
        LSB : bool, optional
            Whether the sourse is in "LSB" mode or not, by default True.
            If `not LSB`, then the incoming bitstream is expected to be in Most Significant Bit first mode and data are transmitted in normal order.
            If `LSB`, then the incoming bitstream is in the format that each 32-bit words are bit-wise reversed on its own.
            Furthermore, the order of 32-bit words in the pixel data within the buffer is reversed (but the order of words in the header is preserved).
            Note that this format does not correspond to the usual LSB-first convention and the parameter name is chosen for the lack of better words.
        buffer_npix : Tuple[int], optional
            A tuple defining how pixels within a single frame is split across multiple buffers, by default (20432, 20432, 20432, 20432, 10688).
            Each number in the tuple represents how many pixels are contained in each buffer.
            The length of the tuple represents the number of buffers a frame is split across.
        pix_depth : int, optional
            Bit-depth of each pixel, by default 8.
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.preamble = preamble
        self.header_fmt = header_fmt
        self.header_len = header_len * 32
        if LSB:
            self.LSB = True
        else:
            self.LSB = False
        self.buffer_npix = buffer_npix
        assert frame_height * frame_width == sum(
            self.buffer_npix
        ), "Number of pixels defined by frame width and height must agree with total number of pixels in `buffer_npix`!"
        self.nbuffer_per_fm = len(self.buffer_npix)
        self.pix_depth = pix_depth

    def _parse_header(
        self, buffer: bytes, truncate: Literal["preamble", "header", False] = False
    ) -> Tuple[MetadataHeader, bytes]:
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
        Tuple[MetadataHeader, bytes]
            The returned header data and (optionally truncated) buffer data.
        """
        pre = Bits(self.preamble)
        if self.LSB:
            pre = pre[::-1]
        pre_len = len(pre)
        assert buffer[:pre_len] == pre
        header_data = dict()
        for hd, bit_range in self.header_fmt.model_dump().items():
            b = buffer[pre_len + bit_range[0] : pre_len + bit_range[1]]
            if self.LSB:
                header_data[hd] = b[::-1].uint
            else:
                header_data[hd] = b.uint

        header_data = MetadataHeader.model_construct(**header_data)

        if truncate == "preamble":
            return header_data, buffer[pre_len:]
        elif truncate == "header":
            return header_data, buffer[pre_len + self.header_len :]
        else:
            return header_data, buffer

    def _uart_recv(
        self, serial_buffer_queue: multiprocessing.Queue, comport: str, baudrate: int
    ):
        """
        Receive buffers and push into serial_buffer_queue

        Parameters
        ----------
        serial_buffer_queue : multiprocessing.Queue
            _description_
        comport : str
            _description_
        baudrate : int
            _description_
        """
        # set up logger
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)

        pre_bytes = bytes(bytearray(self.preamble.tobytes())[::-1])

        file = logging.FileHandler(
            datetime.now().strftime("log/uart_recv/uart_recv_log%Y_%m_%d_%H_%M.log")
        )
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter(
            "%(asctime)s:%(levelname)s:%(message)s", datefmt="%H:%M:%S"
        )
        file.setFormatter(fileformat)

        locallogs.addHandler(file)
        coloredlogs.install(level=logging.INFO, logger=locallogs)

        # set up serial port
        serial_port = serial.Serial(
            port=comport, baudrate=baudrate, timeout=5, stopbits=1
        )
        locallogs.info("Serial port open: " + str(serial_port.name))

        # Throw away the first buffer because it won't fully come in
        uart_bites = serial_port.read_until(pre_bytes)
        log_uart_buffer = BitArray([x for x in uart_bites])

        while 1:
            # read UART data until preamble and put into queue
            uart_bites = serial_port.read_until(pre_bytes)
            log_uart_buffer = [x for x in uart_bites]
            serial_buffer_queue.put(log_uart_buffer)

        time.sleep(1)  # time for ending other process
        serial_port.close()
        print("Close serial port")
        sys.exit(1)

    def _fpga_recv(
        self,
        serial_buffer_queue: multiprocessing.Queue[bytes],
        read_length: int = None,
        pre_first: bool = True,
    ) -> None:
        """
        Function to read bitstream from OpalKelly device and store buffer in `serial_buffer_queue`.

        The bits data are read in fixed chunks defined by `read_length`.
        Then we concatenate the chunks and try to look for `self.preamble` in the data.
        The data between every pair of `self.preamble` is considered to be a single buffer and stored in `serial_buffer_queue`.

        Parameters
        ----------
        serial_buffer_queue : multiprocessing.Queue[bytes]
            The queue holding the buffer data.
        read_length : int, optional
            Length of data to read in chunks (in number of bytes), by default None.
            If `None`, an optimal length is estimated so that it roughly covers a single buffer and is an integer multiple of 16 bytes (as recommended by OpalKelly).
        pre_first : bool, optional
            Whether preamble/header is returned at the beginning of each buffer, by default True.

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
            read_length = int(max(self.buffer_npix) * self.pix_depth / 8 / 16) * 16
        # set up logger
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)
        log_path = "log/fpga_recv/"
        os.makedirs(log_path, exist_ok=True)
        file = logging.FileHandler(
            os.path.join(
                log_path, datetime.now().strftime("fpga_recv_log%Y_%m_%d_%H_%M.log")
            )
        )
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter(
            "%(asctime)s:%(levelname)s:%(message)s", datefmt="%H:%M:%S"
        )
        file.setFormatter(fileformat)
        locallogs.addHandler(file)
        coloredlogs.install(level=logging.INFO, logger=locallogs)
        # set up fpga devices
        dev = okDev()
        dev.setWire(0x00, 0b0010)
        time.sleep(0.01)
        dev.setWire(0x00, 0b0)
        dev.setWire(0x00, 0b1000)
        time.sleep(0.01)
        dev.setWire(0x00, 0b0)
        # read loop
        cur_buffer = BitArray()
        pre = Bits(self.preamble)
        if self.LSB:
            pre = pre[::-1]
        while True:
            buf = dev.readData(read_length)
            dat = BitArray(buf)
            cur_buffer = cur_buffer + dat
            pre_pos = list(cur_buffer.findall(pre))
            for buf_start, buf_stop in zip(pre_pos[:-1], pre_pos[1:]):
                if not pre_first:
                    buf_start, buf_stop = buf_start + len(pre), buf_stop + len(pre)
                serial_buffer_queue.put(cur_buffer[buf_start:buf_stop].tobytes())
            cur_buffer = cur_buffer[pre_pos[-1] :]

    def _buffer_to_frame(
        self,
        serial_buffer_queue: multiprocessing.Queue[bytes],
        frame_buffer_queue: multiprocessing.Queue[list[bytes]],
    ):
        """
        Group buffers together to make frames.

        Pull out buffers in `serial_buffer_queue`, then get frame and buffer index by parsing headers in the buffer.
        The buffers belonging to the same frame are put in the same list at corresponding buffer index.
        The lists representing each frame are then put into `frame_buffer_queue`.

        Parameters
        ----------
        serial_buffer_queue : multiprocessing.Queue[bytes]
            Input buffer queue.
        frame_buffer_queue : multiprocessing.Queue[list[bytes]]
            Output frame queue.
        """
        # set up logger
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)

        file = logging.FileHandler(
            datetime.now().strftime(
                "log/buffer_to_frame/buffer_to_frame_log%Y_%m_%d_%H_%M.log"
            )
        )
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter(
            "%(asctime)s:%(levelname)s:%(message)s", datefmt="%H:%M:%S"
        )
        file.setFormatter(fileformat)

        locallogs.addHandler(file)
        coloredlogs.install(level=logging.INFO, logger=locallogs)

        cur_fm_buffer_index = -1  # Index of buffer within frame
        cur_fm_num = -1  # Frame number

        while 1:
            if (
                serial_buffer_queue.qsize() > 0
            ):  # Higher is safe but lower should be faster.
                serial_buffer = Bits(
                    serial_buffer_queue.get()
                )  # grab one buffer from queue

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
                            "Frame {} started with buffer {}".format(
                                cur_fm_num, cur_fm_buffer_index
                            )
                        )

                # if same frame_num with previous buffer.
                elif (
                    header_data.frame_num == cur_fm_num
                    and header_data.frame_buffer_count > cur_fm_buffer_index
                ):
                    cur_fm_buffer_index = header_data.frame_buffer_count
                    frame_buffer[cur_fm_buffer_index] = serial_buffer.tobytes()
                    locallogs.debug(
                        "----buffer #" + str(cur_fm_buffer_index) + " stored"
                    )

                # if lost frame from buffer -> reset index
                else:
                    cur_fm_buffer_index = 0

    def _format_frame(
        self,
        frame_buffer_queue: multiprocessing.Queue[list[bytes]],
        imagearray: multiprocessing.Queue[np.ndarray],
    ):
        """
        Construct frame from grouped buffers.

        Each frame data is concatenated from a list of buffers in `frame_buffer_queue` according to `buffer_npix`.
        If there is any mismatch between the expected length of each buffer (defined by `buffer_npix`) and the actual length, then the buffer is either truncated or zero-padded at the end to make the length appropriate, and a warning is thrown.
        Finally, the concatenated buffer data are converted into a 1d numpy array with uint8 dtype and put into `imagearray` queue.

        Parameters
        ----------
        frame_buffer_queue : multiprocessing.Queue[list[bytes]]
            Input buffer queue.
        imagearray : multiprocessing.Queue[np.ndarray]
            Output image array queue.
        """
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)

        file = logging.FileHandler(
            datetime.now().strftime(
                "log/format_frame/format_frame_log%Y_%m_%d_%H_%M.log"
            )
        )
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter(
            "%(asctime)s:%(levelname)s:%(message)s", datefmt="%H:%M:%S"
        )
        file.setFormatter(fileformat)

        locallogs.addHandler(file)
        coloredlogs.install(level=logging.INFO, logger=locallogs)

        while 1:
            if frame_buffer_queue.qsize() > 0:  # Higher is safe but lower is fast.
                locallogs.debug("Found frame in queue")

                frame_data = frame_buffer_queue.get()  # pixel data for single frame
                nbit_lost = 0

                for i, npix_expected in enumerate(self.buffer_npix):
                    if frame_data[i] is not None:
                        header_data, fm_dat = self._parse_header(
                            Bits(frame_data[i]), truncate="header"
                        )
                    else:
                        frame_data[i] = Bits(
                            int=0, length=npix_expected * self.pix_depth
                        )
                        nbit_lost += npix_expected
                        continue
                    npix_header = header_data.pixel_count
                    npix_actual = len(fm_dat) / self.pix_depth

                    if npix_actual != npix_expected:
                        if i < len(self.buffer_npix) - 1:
                            locallogs.warning(
                                "Pixel count inconsistent for frame {} buffer {}. Expected: {}, Header: {}, Actual: {}".format(
                                    header_data.frame_num,
                                    header_data.frame_buffer_count,
                                    npix_expected,
                                    npix_header,
                                    npix_actual,
                                )
                            )
                        nbit_expected = npix_expected * self.pix_depth
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
                    self.frame_height * self.frame_width * self.pix_depth
                )

                if self.LSB:
                    pixel_vector = Array(
                        "uint:32",
                        [
                            pixel_vector[i : i + 32][::-1].uint
                            for i in reversed(range(0, len(pixel_vector), 32))
                        ],
                    )
                img = np.frombuffer(pixel_vector.tobytes(), dtype=np.uint8)
                imagearray.put(img)

                locallogs.info(
                    "frame: {}, bits lost: {}".format(header_data.frame_num, nbit_lost)
                )

    # COM port should probably be automatically found but not sure yet how to distinguish with other devices.
    def capture(
        self,
        source: Literal["uart", "fpga"],
        comport: str = "COM3",
        baudrate: int = 1200000,
        read_length: Optional[int] = None,
    ):
        """
        Entry point to start frame capture.

        Parameters
        ----------
        source : Literal[uart, fpga]
            Device source.
        comport : str, optional
            Passed to :function:`~miniscope_io.stream_daq.stream_daq._uart_recv` when `source == "uart"`, by default "COM3".
        baudrate : int, optional
            Passed to :function:`~miniscope_io.stream_daq.stream_daq._uart_recv` when `source == "uart"`, by default 1200000.
        read_length : Optional[int], optional
            Passed to :function:`~miniscope_io.stream_daq.stream_daq._fpga_recv` when `source == "fpga"`, by default None.

        Raises
        ------
        ValueError
            If `source` is not in `("uart", "fpga")`.
        """
        logdirectories = [
            "log",
            "log/uart_recv",
            "log/format_frame",
            "log/buffer_to_frame",
        ]
        for logpath in logdirectories:
            if not os.path.exists(logpath):
                os.makedirs(logpath)
        file = logging.FileHandler(
            datetime.now().strftime("log/logfile%Y_%m_%d_%H_%M.log")
        )
        file.setLevel(logging.DEBUG)
        fileformat = logging.Formatter(
            "%(asctime)s:%(levelname)s:%(message)s", datefmt="%H:%M:%S"
        )
        file.setFormatter(fileformat)

        globallogs = logging.getLogger(__name__)
        globallogs.setLevel(logging.DEBUG)

        globallogs.addHandler(file)
        coloredlogs.install(level=logging.DEBUG, logger=globallogs)

        # Queue size is hard coded
        queue_manager = multiprocessing.Manager()
        serial_buffer_queue = queue_manager.Queue(
            10
        )  # b'\x00' # hand over single buffer: uart_recv() -> buffer_to_frame()
        frame_buffer_queue = queue_manager.Queue(
            5
        )  # [b'\x00', b'\x00', b'\x00', b'\x00', b'\x00'] # hand over a frame (five buffers): buffer_to_frame()
        imagearray = queue_manager.Queue(5)
        imagearray.put(np.zeros(int(self.frame_width * self.frame_height), np.uint8))

        if source == "uart":
            p_recv = multiprocessing.Process(
                target=self._uart_recv,
                args=(
                    serial_buffer_queue,
                    comport,
                    baudrate,
                ),
            )
        elif source == "fpga":
            p_recv = multiprocessing.Process(
                target=self._fpga_recv,
                args=(
                    serial_buffer_queue,
                    read_length,
                ),
            )
        else:
            raise ValueError(f"source can be one of uart or fpga. Got {source}")

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
        p_recv.start()
        p_buffer_to_frame.start()
        p_format_frame.start()

        while (
            1
        ):  # Seems like GUI functions should be on main thread in scripts but not sure what it means for this case
            if imagearray.qsize() > 0:
                imagearray_plot = imagearray.get()
                image = imagearray_plot.reshape(self.frame_width, self.frame_height)
                # np.savetxt('imagearray.csv', imagearray, delimiter=',')
                # np.savetxt('image.csv', image, delimiter=',')
                cv2.imshow("image", image)
            if cv2.waitKey(1) == 27:
                cv2.destroyAllWindows()
                cv2.waitKey(100)
                break  # esc to quit
        print("End capture")

        while True:
            print("[Terminating] uart/fpga_recv()")
            p_recv.terminate()
            time.sleep(0.1)
            if not p_recv.is_alive():
                p_recv.join(timeout=1.0)
                print("[Terminated] uart/fpga_recv()")
                break  # watchdog process daemon gets [Terminated]

        while True:
            print("[Terminating] buffer_to_frame()")
            p_buffer_to_frame.terminate()
            time.sleep(0.1)
            if not p_buffer_to_frame.is_alive():
                p_buffer_to_frame.join(timeout=1.0)
                print("[Terminated] buffer_to_frame()")
                break  # watchdog process daemon gets [Terminated]

        while True:
            print("[Terminating] format_frame()")
            p_format_frame.terminate()
            time.sleep(0.1)
            if not p_format_frame.is_alive():
                p_format_frame.join(timeout=1.0)
                print("[Terminated] format_frame()")
                break  # watchdog process daemon gets [Terminated]


def updateDevice():
    args = updateDeviceParser.parse_args()
    moduleList = ["LED", "EWL"]

    ledMAX = 100
    ledMIN = 0

    ewlMAX = 255
    ewlMIN = 0

    ledDeviceTag = 0  # 2-bits each for now
    ewlDeviceTag = 1  # 2-bits each for now

    deviceTagPos = 4
    preamblePos = 6

    Preamble = [2, 1]  # 2-bits each for now

    uartPayload = 4
    uartRepeat = 5
    uartTimeGap = 0.01

    try:
        assert len(vars(args)) == 4
    except AssertionError as msg:
        print(msg)
        print("Usage: updateDevice [COM port] [baudrate] [module] [value]")
        sys.exit(1)

    try:
        comport = str(args.port)
    except (ValueError, IndexError) as e:
        print(e)
        sys.exit(1)

    try:
        baudrate = int(args.baudrate)
    except (ValueError, IndexError) as e:
        print(e)
        sys.exit(1)

    try:
        module = str(args.module)
        assert module in moduleList
    except AssertionError as msg:
        print(msg)
        print("Available modules:")
        for module in moduleList:
            print("\t" + module)
        sys.exit(1)

    try:
        value = int(args.value)
    except Exception as e:
        print(e)
        print("Value needs to be an integer")
        sys.exit(1)

    try:
        if module == "LED":
            assert value <= ledMAX and value >= ledMIN
        if module == "EWL":
            assert value <= ewlMAX and value >= ewlMIN
    except AssertionError as msg:
        print(msg)
        if module == "LED":
            print("LED value need to be a integer within 0-100")
        if module == "EWL":
            print("EWL value need to be an integer within 0-255")
        sys.exit(1)

    if module == "LED":
        deviceTag = ledDeviceTag << deviceTagPos
    elif module == "EWL":
        deviceTag = ewlDeviceTag << deviceTagPos

    command = [0, 0]

    command[0] = int(
        Preamble[0] * 2**preamblePos
        + deviceTag
        + np.floor(value / (2**uartPayload))
    ).to_bytes(1, "big")
    command[1] = int(
        Preamble[1] * 2**preamblePos + deviceTag + value % (2**uartPayload)
    ).to_bytes(1, "big")

    # set up serial port
    try:
        serial_port = serial.Serial(
            port=comport, baudrate=baudrate, timeout=5, stopbits=1
        )
    except Exception as e:
        print(e)
        sys.exit(1)
    print("Open serial port")

    for uartCommand in command:
        for repeat in range(uartRepeat):
            # read UART data until preamble and put into queue
            serial_port.write(uartCommand)
            time.sleep(uartTimeGap)

    serial_port.close()
    print("\t" + module + ": " + str(value))
    print("Close serial port")
    sys.exit(1)


def main():
    daq_inst = stream_daq()
    args = daqParser.parse_args()

    if args.source == "UART":
        try:
            assert len(vars(args)) == 3
        except AssertionError as msg:
            print(msg)
            print("Usage: stream_image_capture --port [COM port] --baudrate [baudrate]")
            sys.exit(1)

        try:
            comport = str(args.port)
        except (ValueError, IndexError) as e:
            print(e)
            sys.exit(1)

        try:
            baudrate = int(args.baudrate)
        except (ValueError, IndexError) as e:
            print(e)
            sys.exit(1)
        daq_inst.capture(source="uart", comport=comport, baudrate=baudrate)

    if args.source == "OK":
        HAVE_OK = False
        try:
            from miniscope_io.devices.opalkelly import okDev

            HAVE_OK = True
        except (ImportError, ModuleNotFoundError) as e:
            warnings.warn(f"Cannot import OpalKelly device, got exception {e}")

        daq_inst.capture(source="fpga")


if __name__ == "__main__":
    main()
