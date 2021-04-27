# -- coding: utf-8 --

from pyftdi.spi import SpiController
from hardware.diy_daq import cpp_header_parser


class MAX113XX:
    configDesignVals = ["gpo_data_15_to_0_DESIGNVALUE",
                        "gpo_data_19_to_16_DESIGNVALUE",
                        0,  # reserved
                        "device_control_DESIGNVALUE",
                        "interrupt_mask_DESIGNVALUE",
                        "gpi_irqmode_7_to_0_DESIGNVALUE",
                        "gpi_irqmode_15_to_8_DESIGNVALUE",
                        "gpi_irqmode_19_to_16_DESIGNVALUE",
                        0,  # reserved
                        "dac_preset_data_1_DESIGNVALUE",
                        "dac_preset_data_2_DESIGNVALUE",
                        "tmp_mon_cfg_DESIGNVALUE",
                        "tmp_mon_int_hi_thresh_DESIGNVALUE",
                        "tmp_mon_int_lo_thresh_DESIGNVALUE",
                        "tmp_mon_ext1_hi_thresh_DESIGNVALUE",
                        "tmp_mon_ext1_lo_thresh_DESIGNVALUE",
                        "tmp_mon_ext2_hi_thresh_DESIGNVALUE",
                        "tmp_mon_ext2_lo_thresh_DESIGNVALUE"]

    portConfigDesignVals = [f'port_cfg_{i:02}_DESIGNVALUE' for i in range(20)]
    dacDesignVals = [f'dac_data_port_{i:02}_DESIGNVALUE' for i in range(20)]

    def __init__(self, ftdi_interface, ccp_header_file):
        self.ftdi_interface = ftdi_interface
        self.ccp_header_file = ccp_header_file

        self.setConfigure()

    def setConfigure(self):
        self.spi = SpiController()
        self.spi.configure(self.ftdi_interface)

        self.slave = self.spi.get_port(cs=0, freq=12E6, mode=0)

        self.ccp_header = cpp_header_parser.read_header(self.ccp_header_file)

        self.blockWrite(
            self.ccp_header["gpo_data_15_to_0"],
            self.makeup_data(
                self.configDesignVals))
        self.blockWrite(
            self.ccp_header["port_cfg_00"],
            self.makeup_data(
                self.portConfigDesignVals))
        self.blockWrite(
            self.ccp_header["dac_data_port_00"],
            self.makeup_data(
                self.dacDesignVals))

    def makeup_data(self, keylist):
        return [self.ReadFromCppHeader(key) for key in keylist]

    def ReadFromCppHeader(self, val):
        try:
            if val in self.ccp_header.keys():
                return self.ccp_header[val]
            else:
                return val
        except NameError:
            print("You should execute setConfigure()")
            return val

    def MAX113XXAddr_SPI_Write(self, reg):
        """
        SPI first byte when writing MAX11300/11
        (7-bit address in bits 0x7E; LSB=0 for write)
        """
        RegAddr = self.ReadFromCppHeader(reg)
        return (RegAddr << 1)

    def MAX113XXAddr_SPI_Read(self, reg):
        """
        SPI first byte when reading MAX11300/11
        (7-bit address in bits 0x7E; LSB=1 for read)
        """
        RegAddr = self.ReadFromCppHeader(reg)
        return ((RegAddr << 1) | 1)

    def writeRegister(self, reg, data):
        tx_reg = self.MAX113XXAddr_SPI_Write(reg)
        tx_buf = [tx_reg, ((0xFF00 & data) >> 8), (0x00FF & data)]

        self.slave.exchange(tx_buf, readlen=0, duplex=True)

    def readRegister(self, reg):
        tx_reg = self.MAX113XXAddr_SPI_Read(reg)
        tx_buf = [tx_reg, 0x00, 0x00]
        # 0x0000 is dummy data.

        rx_buf = self.slave.exchange(tx_buf, readlen=3, duplex=True)

        rtn_val = (rx_buf[1] << 8) | rx_buf[2]
        # rx_buf is [0xff, MSB data, LSB data].
        return rtn_val

    def blockWrite(self, reg, data):
        tx_reg = self.MAX113XXAddr_SPI_Write(reg)
        tx_buf = [tx_reg]

        for data_buf in data:
            tx_buf.append((0xFF00 & data_buf) >> 8)
            tx_buf.append((0x00FF & data_buf))

        self.slave.exchange(tx_buf, readlen=0, duplex=True)

    def blockRead(self, reg, num_reg):
        tx_reg = self.MAX113XXAddr_SPI_Read(reg)
        tx_buf = [tx_reg] + [0x00] * (2 * num_reg)

        rx_buf = self.slave.exchange(tx_buf, readlen=(1 + 2 * num_reg), duplex=True)

        rtn_data = []
        for idx in range(num_reg):
            rtn_data.append((rx_buf[2 * idx + 1] << 8) | rx_buf[2 * idx + 2])

        return rtn_data

    def dumpMemory(self):
        mem = self.blockRead(0x00, 0x74)
        for idx, data in enumerate(mem):
            print('Register 0x{:02X} = 0x{:04X}'.format(idx, data))


if __name__ == "__main__":
    from pyftdi.ftdi import Ftdi
    Ftdi.show_devices()

    max11300 = MAX113XX('ftdi://ftdi:2232:0:1/1',
                 r"hardware\diy_daq\MAX11300Hex.h")
    max11300.dumpMemory()
