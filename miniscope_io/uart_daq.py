import argparse
import logging
import multiprocessing
import os
import sys
import time
from datetime import datetime
import warnings
from typing import Literal

import coloredlogs
import cv2
import numpy as np
import serial
from bitstring import Array, BitArray, Bits

HAVE_OK = False
try:
    from miniscope_io.devices.opalkelly import okDev
    HAVE_OK = True
except (ImportError, ModuleNotFoundError) as e:
    warnings.warn(f'Cannot import OpalKelly device, got exception {e}')

# Parsers for daq inputs
daqParser = argparse.ArgumentParser("uart_image_capture")
daqParser.add_argument("port", help="serial port")
daqParser.add_argument("baudrate", help="baudrate")

# Parsers for update LED
updateDeviceParser = argparse.ArgumentParser("updateDevice")
updateDeviceParser.add_argument("port", help="serial port")
updateDeviceParser.add_argument("baudrate", help="baudrate")
updateDeviceParser.add_argument("module", help="module to update")
updateDeviceParser.add_argument("value", help="LED value")


class uart_daq:
    """
    A combined class for reading frames from a UART and FPGA source.

    .. todo::

        Phil/Takuya - docstrings for uart daq: what devices these correspond to, how to configure them, usage examples, tests

    """
    def __init__(
        self,
        frame_width: int = 304,
        frame_height: int = 304,
        preamble=b"\x12\x34\x56",
        header_fmt={
            "FRAME_NUM": (32, 64),
            "BUFFER_COUNT": (64, 96),
            "LINKED_LIST": (0, 32),
            "FRAME_BUFFER_COUNT": (96, 128),
            "PIXEL_COUNT": (224, 256),
            "TIMESTAMP": (192, 224),
        },
        header_len=11,
        LSB=True,
        buffer_npix=[20432, 20432, 20432, 20432, 10688],
        pix_depth=8,
    ):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.preamble = Bits(preamble)
        self.header_fmt = header_fmt
        self.header_len = header_len * 32
        self.LSB = LSB
        self.buffer_npix = buffer_npix
        assert frame_height * frame_width == sum(self.buffer_npix)
        self.nbuffer_per_fm = len(self.buffer_npix)
        self.pix_depth = pix_depth

    def _parse_header(self, buffer, truncate=False):
        pre_len = len(self.preamble)
        if self.LSB:
            assert buffer[:pre_len][::-1] == self.preamble
        else:
            assert buffer[:pre_len] == self.preamble
        header_data = dict()
        for hd, bit_range in self.header_fmt.items():
            b = buffer[pre_len + bit_range[0] : pre_len + bit_range[1]]
            if self.LSB:
                header_data[hd] = b[::-1].uint
            else:
                header_data[hd] = b.uint
        if truncate == "preamble":
            return header_data, buffer[pre_len:]
        elif truncate == "header":
            return header_data, buffer[pre_len + self.header_len :]
        else:
            return header_data, buffer

    # Receive buffers and push into serial_buffer_queue
    def _uart_recv(self, serial_buffer_queue, comport: str, baudrate: int):
        # set up logger
        locallogs = logging.getLogger(__name__)
        locallogs.setLevel(logging.DEBUG)

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
        log_uart_buffer = bytearray(serial_port.read_until(self.preamble))

        while 1:
            # read UART data until preamble and put into queue
            log_uart_buffer = bytearray(serial_port.read_until(self.preamble))
            serial_buffer_queue.put(log_uart_buffer)

        time.sleep(1)  # time for ending other process
        serial_port.close()
        print("Close serial port")
        sys.exit(1)

    def _fpga_recv(
        self, serial_buffer_queue, read_length=None, pre_first=True
    ):
        if not HAVE_OK:
            raise RuntimeError('Couldnt import OpalKelly device. Check the docs for install instructions!')
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
        pre = Bits(self.preamble)[::-1]
        while True:
            buf = dev.readData(read_length)
            dat = BitArray(buf)
            cur_buffer = cur_buffer + dat
            pre_pos = list(cur_buffer.findall(pre))
            for buf_start, buf_stop in zip(pre_pos[:-1], pre_pos[1:]):
                if not pre_first:
                    buf_start, buf_stop = buf_start + len(pre), buf_stop + len(pre)
                serial_buffer_queue.put(cur_buffer[buf_start:buf_stop])
            cur_buffer = cur_buffer[pre_pos[-1] :]

    # Pull out data buffers from serial_buffer_queue
    # Make a list of buffers forming a frame and push into frame_buffer_queue
    def _buffer_to_frame(self, serial_buffer_queue, frame_buffer_queue):
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
                serial_buffer = serial_buffer_queue.get()  # grab one buffer from queue

                header_data, serial_buffer = self._parse_header(serial_buffer)

                # log metadata
                locallogs.debug(str(header_data))

                # if first buffer of a frame
                if header_data["FRAME_NUM"] != cur_fm_num:
                    # discard first incomplete frame
                    if cur_fm_num == -1 and header_data["FRAME_BUFFER_COUNT"] != 0:
                        continue

                    # push frame_buffer into frame_buffer queue
                    frame_buffer_queue.put(frame_buffer)
                    # init frame_buffer
                    frame_buffer = [None] * self.nbuffer_per_fm

                    # update frame_num and index
                    cur_fm_num = header_data["FRAME_NUM"]
                    cur_fm_buffer_index = header_data["FRAME_BUFFER_COUNT"]

                    # update data
                    frame_buffer[cur_fm_buffer_index] = serial_buffer

                    if cur_fm_buffer_index != 0:
                        locallogs.warning(
                            "Frame {} started with buffer {}".format(
                                cur_fm_num, cur_fm_buffer_index
                            )
                        )

                # if same frame_num with previous buffer.
                elif (
                    header_data["FRAME_NUM"] == cur_fm_num
                    and header_data["FRAME_BUFFER_COUNT"] > cur_fm_buffer_index
                ):
                    cur_fm_buffer_index = header_data["FRAME_BUFFER_COUNT"]
                    frame_buffer[cur_fm_buffer_index] = serial_buffer
                    locallogs.debug(
                        "----buffer #" + str(cur_fm_buffer_index) + " stored"
                    )

                # if lost frame from buffer -> reset index
                else:
                    cur_fm_buffer_index = 0

    def _format_frame(self, frame_buffer_queue, imagearray):
        pixel_order_flip = False
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
                            frame_data[i], truncate="header"
                        )
                    else:
                        frame_data[i] = Bits(
                            int=0, length=npix_expected * self.pix_depth
                        )
                        nbit_lost += npix_expected
                        continue
                    npix_header = header_data["PIXEL_COUNT"]
                    npix_actual = len(fm_dat) / self.pix_depth

                    if npix_actual != npix_expected:
                        if i < len(self.buffer_npix) - 1:
                            locallogs.warning(
                                "Pixel count inconsistent for frame {} buffer {}. Expected: {}, Header: {}, Actual: {}".format(
                                    header_data["FRAME_NUM"],
                                    header_data["FRAME_BUFFER_COUNT"],
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
                            for i in range(0, len(pixel_vector, 32))
                        ],
                    )
                img = np.frombuffer(pixel_vector.tobytes(), dtype=np.uint8)
                imagearray.put(img)

                locallogs.info(
                    "frame: {}, bits lost: {}".format(
                        header_data["FRAME_NUM"], nbit_lost
                    )
                )

    # COM port should probably be automatically found but not sure yet how to distinguish with other devices.
    def capture(
        self,
        source: Literal['uart', 'fpga'],
        comport: str = "COM3",
        baudrate: int = 1200000,
        mode: str = "DEBUG",
        read_length: int = None,
    ):
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
            raise ValueError(f'source can be one of uart or fpga. Got {source}')

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
            print("[Terminating] uart_recv()")
            p_recv.terminate()
            time.sleep(0.1)
            if not p_recv.is_alive():
                p_recv.join(timeout=1.0)
                print("[Terminated] uart_recv()")
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
    # args = daqParser.parse_args()

    # try:
    #     assert len(vars(args)) == 2
    # except AssertionError as msg:
    #     print(msg)
    #     print("Usage: uart_image_capture [COM port] [baudrate]")
    #     sys.exit(1)

    # try:
    #     comport = str(args.port)
    # except (ValueError, IndexError) as e:
    #     print(e)
    #     sys.exit(1)

    # try:
    #     baudrate = int(args.baudrate)
    # except (ValueError, IndexError) as e:
    #     print(e)
    #     sys.exit(1)

    daq_inst = uart_daq()
    daq_inst.capture(source="fpga")


if __name__ == "__main__":
    main()
