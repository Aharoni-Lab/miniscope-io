

from miniscope_io.vendor import opalkelly as ok
from miniscope_io.exceptions import StreamReadError, DeviceConfigurationError, DeviceOpenError
from miniscope_io.logging import init_logger


class okDev(ok.okCFrontPanel):
    """
    I/O and configuration for an (what kind of opal kelly device?)

    .. todo::

        Phil: document what this thing does, including how bitfiles work
        and how they're generated/where they're located.

    """
    def __init__(self, serial_id: str = ""):
        super().__init__()
        self.logger = init_logger('okDev')
        ret = self.OpenBySerial("")
        if ret != self.NoError:
            raise DeviceOpenError("Cannot open device: {}".format(serial_id))
        self.info = ok.okTDeviceInfo()
        ret = self.GetDeviceInfo(self.info)
        if ret == self.NoError:
            self.logger.info("Connected to {}".format(self.info.productName))

    def uploadBit(self, bit_file: str):

        ret = self.ConfigureFPGA(bit_file)
        if ret == self.NoError:
            self.logger.debug("Succesfully uploaded {}".format(bit_file))
        else:
            raise DeviceConfigurationError("Configuration of {} failed".format(self.info.productName))
        self.logger.debug(
            "FrontPanel {} supported".format(
                "is" if self.IsFrontPanelEnabled() else "not"
            )
        )
        ret = self.ResetFPGA()

    def readData(self, length: int, addr: int = 0xA0, blockSize: int = 16) -> bytearray:
        buf = bytearray(length)
        ret = self.ReadFromBlockPipeOut(addr, data=buf, blockSize=blockSize)
        if ret < 0:
            msg = f"Read failed: {ret}"
            self.logger.error(msg)
            raise StreamReadError(msg)
        elif ret < length:
            self.logger.warning(f"Only {ret} bytes read")
        return buf

    def setWire(self, addr: int, val: int):
        ret = self.SetWireInValue(addr, val)
        ret = self.UpdateWireIns()
        if ret != self.NoError:
            raise DeviceConfigurationError("Wire update failed: {}".format(ret))
