"""
Interfaces for OpalKelly (model number?) FPGAs
"""

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
        ret = self.OpenBySerial("")
        if ret != self.NoError:
            raise ValueError(f"Cannot open device: {serial_id}")
        self.info = ok.okTDeviceInfo()
        ret = self.GetDeviceInfo(self.info)
        if ret == self.NoError:
            print(f"Connected to {self.info.productName}")

    def uploadBit(self, bit_file: str) -> None:
        """
        Upload a configuration bitfile to the FPGA

        Args:
            bit_file (str): Path to the bitfile
        """

        ret = self.ConfigureFPGA(bit_file)
        if ret == self.NoError:
            print(f"Succesfully uploaded {bit_file}")
        else:
            raise ValueError(f"Configuration of {self.info.productName} failed")
        print(
            "FrontPanel {} supported".format(
                "is" if self.IsFrontPanelEnabled() else "not"
            )
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
            raise ValueError(f"Read failed: {ret}")
        elif ret < length:
            print(f"Only {ret} bytes read")
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
            raise ValueError(f"Wire update failed: {ret}")
