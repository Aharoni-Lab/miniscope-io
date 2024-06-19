from pathlib import Path
from typing import Dict

from ..conftest import DATA_DIR

from miniscope_io.exceptions import EndOfRecordingException

class okDevMock():
    """
    Mock class for :class:`~miniscope_io.devices.opalkelly.okDev`
    """
    DATA_FILE = DATA_DIR / 'stream_daq_test_fpga_raw_input_200px.bin'
    """
    Recorded data file to use for simulating read.
    
    Set as class variable so that it can be monkeypatched in tests that
    require different source data files
    """

    def __init__(self, serial_id: str = ""):
        self.serial_id = serial_id
        self.bit_file = None

        self._wires: Dict[int, int] = {}
        self._buffer_position = 0

        # preload the data file to a byte array
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





