import os
from pathlib import Path
from typing import Dict

from miniscope_io.exceptions import EndOfRecordingException

class okDevMock():
    """
    Mock class for :class:`~miniscope_io.devices.opalkelly.okDev`
    """
    DATA_FILE = None
    """
    Recorded data file to use for simulating read.
    
    Set as class variable so that it can be monkeypatched in tests that
    require different source data files.
    
    Can be set using the ``PYTEST_OKDEV_DATA_FILE`` environment variable if 
    this mock is to be used within a separate process.
    """

    def __init__(self, serial_id: str = ""):
        self.serial_id = serial_id
        self.bit_file = None

        self._wires: Dict[int, int] = {}
        self._buffer_position = 0

        # preload the data file to a byte array
        if self.DATA_FILE is None:
            if os.environ.get("PYTEST_OKDEV_DATA_FILE", False):
                # need to get file from env variables here because on some platforms
                # the default method for creating a new process is "spawn" which creates
                # an entirely new python session instead of "fork" which would preserve
                # the classvar
                okDevMock.DATA_FILE = Path(os.environ.get("PYTEST_OKDEV_DATA_FILE"))
            else:
                raise RuntimeError('DATA_FILE class attr must be set before using the mock')

        with open(self.DATA_FILE, 'rb') as dfile:
            self._buffer = bytearray(dfile.read())



    def uploadBit(self, bit_file: str):
        assert Path(bit_file).exists()
        self.bit_file = bit_file

    def readData(self, length: int, addr: int = 0xA0, blockSize: int = 16) -> bytearray:
        if self._buffer_position >= len(self._buffer):
            # Error if called after we have returned the last data
            raise EndOfRecordingException('End of sample buffer')

        end_pos = min(self._buffer_position + length, len(self._buffer))
        data = self._buffer[self._buffer_position:end_pos]
        self._buffer_position = end_pos
        return data

    def setWire(self, addr: int, val: int):
        self._wires[addr] = val