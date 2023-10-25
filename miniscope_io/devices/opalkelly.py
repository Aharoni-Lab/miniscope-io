import time

from bitstring import BitArray

from miniscope_io.vendor.opalkelly.lib import ok


class okDev(ok.okCFrontPanel):
    def __init__(self, serial_id: str = ""):
        super().__init__()
        ret = self.OpenBySerial("")
        if ret != self.NoError:
            raise ValueError("Cannot open device: {}".format(serial_id))
        self.info = ok.okTDeviceInfo()
        ret = self.GetDeviceInfo(self.info)
        if ret == self.NoError:
            print("Connected to {}".format(self.info.productName))

    def uploadBit(self, bit_file: str):
        ret = self.ConfigureFPGA(bit_file)
        if ret == self.NoError:
            print("Succesfully uploaded {}".format(bit_file))
        else:
            raise ValueError("Configuration of {} failed".format(self.info.productName))
        print(
            "FrontPanel {} supported".format(
                "is" if self.IsFrontPanelEnabled() else "not"
            )
        )
        ret = self.ResetFPGA()

    def readData(self, length: int, addr: int = 0xA0, blockSize: int = 16):
        buf = bytearray(length)
        ret = self.ReadFromBlockPipeOut(addr, data=buf, blockSize=blockSize)
        if ret < 0:
            raise ValueError("Read failed: {}".format(ret))
        elif ret < length:
            print("Only {} bytes read".format(ret))
        return buf

    def setWire(self, addr: int, val: int):
        ret = self.SetWireInValue(addr, val)
        ret = self.UpdateWireIns()
        if ret != self.NoError:
            raise ValueError("Wire update failed: {}".format(ret))
