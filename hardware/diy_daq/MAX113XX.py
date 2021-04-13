# -- coding: utf-8 --

from pyftdi.spi import SpiController
from hardware.diy_daq import cpp_header_parser

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


def setConfigure(ftdi_interface, ccp_header_file):
    spi = SpiController()
    spi.configure(ftdi_interface)
    global slave
    slave = spi.get_port(cs=0, freq=12E6, mode=0)

    global ccp_header
    ccp_header = cpp_header_parser.read_header(ccp_header_file)

    def makeup_data(keylist):
        return [ReadFromCppHeader(key) for key in keylist]

    blockWrite(ccp_header["gpo_data_15_to_0"], makeup_data(configDesignVals))
    blockWrite(ccp_header["port_cfg_00"], makeup_data(portConfigDesignVals))
    blockWrite(ccp_header["dac_data_port_00"], makeup_data(dacDesignVals))


def ReadFromCppHeader(val):
    try:
        if val in ccp_header.keys():
            return ccp_header[val]
        else:
            return val
    except NameError:
        print("You should execute setConfigure()")
        return val


def MAX113XXAddr_SPI_Write(reg):
    """
    SPI first byte when writing MAX11300/11
    (7-bit address in bits 0x7E; LSB=0 for write)
    """
    RegAddr = ReadFromCppHeader(reg)
    return (RegAddr << 1)


def MAX113XXAddr_SPI_Read(reg):
    """
    SPI first byte when reading MAX11300/11
    (7-bit address in bits 0x7E; LSB=1 for read)
    """
    RegAddr = ReadFromCppHeader(reg)
    return ((RegAddr << 1) | 1)


def writeRegister(reg, data):
    tx_reg = MAX113XXAddr_SPI_Write(reg)
    tx_buf = [tx_reg, ((0xFF00 & data) >> 8), (0x00FF & data)]

    rx_buf = slave.exchange(tx_buf, readlen=3, duplex=True)
    # STM32では、tx_reg送ってからdata送る必要があったから、もしかすると分割する必要があるかもしれない。


def readRegister(reg):
    tx_reg = MAX113XXAddr_SPI_Read(reg)
    tx_buf = [tx_reg, 0x00, 0x00]
    # 0x0000 is dummy data.

    rx_buf = slave.exchange(tx_buf, readlen=3, duplex=True)
    # STM32では、tx_reg送ってからdata送る必要があったから、もしかすると分割する必要があるかもしれない。
    rtn_val = (rx_buf[1] << 8) | rx_buf[2]
    # rx_buf is [0xff, MSB data, LSB data].
    return rtn_val


def blockWrite(reg, data):
    tx_reg = MAX113XXAddr_SPI_Write(reg)
    tx_buf = [tx_reg]

    for data_buf in data:
        tx_buf.append((0xFF00 & data_buf) >> 8)
        tx_buf.append((0x00FF & data_buf))

    slave.exchange(tx_buf, readlen=0, duplex=True)


def blockRead(reg, num_reg):
    tx_reg = MAX113XXAddr_SPI_Read(reg)
    tx_buf = [tx_reg] + [0x00] * (2 * num_reg)

    rx_buf = slave.exchange(tx_buf, readlen=(1 + 2 * num_reg), duplex=True)
    # STM32では、tx_reg送ってからdata送る必要があったから、もしかすると分割する必要があるかもしれない。

    rtn_data = []
    for idx in range(num_reg):
        rtn_data.append((rx_buf[2 * idx + 1] << 8) | rx_buf[2 * idx + 2])

    return rtn_data


def dumpMemory():
    mem = blockRead(0x00, 0x74)
    for idx, data in enumerate(mem):
        print('Register 0x{:02X} = 0x{:04X}'.format(idx, data))


if __name__ == "__main__":
    from pyftdi.ftdi import Ftdi
    Ftdi.show_devices()

    setConfigure('ftdi://ftdi:2232:0:1/1',
                 r"hardware\diy_daq\MAX11300Hex.h")
    dumpMemory()
