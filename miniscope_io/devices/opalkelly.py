"""
Interfaces for OpalKelly (model number?) FPGAs
"""

import multiprocessing as mp
import os
from pathlib import Path
from time import sleep
from typing import Callable

from bitstring import Bits

from miniscope_io.devices.mocks import okDevMock
from miniscope_io.exceptions import (
    DeviceConfigurationError,
    DeviceOpenError,
    EndOfRecordingException,
    StreamReadError,
)
from miniscope_io.logging import init_logger
from miniscope_io.vendor import opalkelly as ok


class okDev(ok.okCFrontPanel):
    """
    I/O and configuration for an (what kind of opal kelly device?)

    .. todo::

        Phil: document what this thing does, including how bitfiles work
        and how they're generated/where they're located.

    """

    def __init__(self, serial_id: str = ""):
        super().__init__()
        self.logger = init_logger("okDev")
        ret = self.OpenBySerial("")
        if ret != self.NoError:
            raise DeviceOpenError(f"Cannot open device: {serial_id}")
        self.info = ok.okTDeviceInfo()
        ret = self.GetDeviceInfo(self.info)
        if ret == self.NoError:
            self.logger.info(f"Connected to {self.info.productName}")

    def uploadBit(self, bit_file: str) -> None:
        """
        Upload a configuration bitfile to the FPGA

        Args:
            bit_file (str): Path to the bitfile
        """

        ret = self.ConfigureFPGA(bit_file)
        if ret == self.NoError:
            self.logger.debug(f"Succesfully uploaded {bit_file}")
        else:
            raise DeviceConfigurationError(f"Configuration of {self.info.productName} failed")
        self.logger.debug(
            "FrontPanel {} supported".format("is" if self.IsFrontPanelEnabled() else "not")
        )
        ret = self.ResetFPGA()

    def readData(self, length: int, addr: int = 0xA0, blockSize: int = 16) -> bytearray:
        """
        Read a buffer's worth of data

        Args:
            length (int): Amount of data to read
            addr (int): FPGA address to read from
            blockSize (int): Size of individual blocks (in what unit?)

        Returns:
            :class:`bytearray`
        """
        buf = bytearray(length)
        ret = self.ReadFromBlockPipeOut(addr, data=buf, blockSize=blockSize)
        if ret < 0:
            msg = f"Read failed: {ret}"
            self.logger.error(msg)
            raise StreamReadError(msg)
        elif ret < length:
            self.logger.warning(f"Only {ret} bytes read")
        return buf

    def setWire(self, addr: int, val: int) -> None:
        """
        .. todo::

            Phil! what does this do?

        Args:
            addr: ?
            val: ?
        """
        ret = self.SetWireInValue(addr, val)
        ret = self.UpdateWireIns()
        if ret != self.NoError:
            raise DeviceConfigurationError(f"Wire update failed: {ret}")


class okCapture:
    """
    Capture class for :class:`.okDev` that pipes minimally formatted buffers
    to a multiprocessing queue or dequeue
    """

    def __init__(self, bit_file: Path, read_length: int, preamble: bytes):

        self.bit_file = Path(bit_file)
        self.read_length = read_length
        self.preamble = Bits(preamble)
        self.dev: okDev | okDevMock | None = None

        self.terminate = mp.Event()

    def capture(
        self, callback: Callable[[bytearray | None], None], process: bool = True
    ) -> mp.Process | None:
        """
        Begin capturing frames
        Args:
            callback (Callable): call this function with each buffer received by the device
            process (bool): If ``True`` (default), run in a separate process

        """
        if process:
            proc = mp.Process(target=self._capture_loop, args=(callback,))
            proc.start()
            return proc
        else:
            self._capture_loop(callback=callback)

    def _capture(self) -> bytearray | None:
        """Inner capture method, get and return a bytestring from the device"""
        locallogs = init_logger("okCapture.capture")
        try:
            buf = self.dev.readData(self.read_length)
        except (EndOfRecordingException, StreamReadError, KeyboardInterrupt):
            locallogs.debug("Got end of recording exception, breaking")
            return None

        return buf

    def _capture_loop(self, callback: Callable[[bytearray | None], None]) -> None:
        """
        Capture a byte string and call the callback function until we are told to end
        """
        locallogs = init_logger("okCapture.capture_loop")
        locallogs.debug("Initializing okDev")
        self.dev = self.init_device()
        locallogs.debug("Starting capture")
        try:
            while not self.terminate.is_set():
                buffer = self._capture()
                if buffer is None:
                    break
                callback(buffer)
        finally:
            locallogs.debug("Quitting, putting sentinel in queue")
            callback(None)

    def stop(self) -> None:
        """
        Stop capture
        """
        self.terminate.set()

    def init_device(self) -> okDev | okDevMock:
        """Write initialization wires to prepare okDev for streaming data"""
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("STREAMDAQ_MOCKRUN"):
            dev = okDevMock()
        else:
            dev = okDev()

        if not self.bit_file.exists():
            raise RuntimeError(
                f"Configured to use bitfile at {self.bit_file} but no such file exists"
            )

        dev.uploadBit(str(self.bit_file))
        dev.setWire(0x00, 0b0010)
        sleep(0.01)
        dev.setWire(0x00, 0b0)
        dev.setWire(0x00, 0b1000)
        sleep(0.01)
        dev.setWire(0x00, 0b0)
        return dev
