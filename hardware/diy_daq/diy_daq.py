# -*- coding: utf-8 -*-
"""
Arios ATC-204(東邦電子 TTM-204)制御用コード

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

from core.module import Base
from core.connector import Connector
from core.configoption import ConfigOption
from interface.process_interface import ProcessInterface
from interface.process_control_interface import ProcessControlInterface

from pyftdi.ftdi import Ftdi
from hardware.diy_daq.MAX113XX import MAX113XX

import serial
import time


class DIY_DAQ(Base, ProcessInterface, ProcessControlInterface):
    """ Methods to control Arios ATC-204(東邦電子 TTM-204).
    https://dia-pe-titech.esa.io/posts/158

    Example config for copy-paste:

    DIY_DAQ:
        module.Class: 'diy_daq.diy_daq.DIY_DAQ'
        port: 'COM4'
        ftdi_interface: "ftdi:///1"
        ccp_header_file: r"hardware\diy_daq\MAX11300Hex.h"

        limit_min: 0    # Pa
        limit_max: 40e3 # Pa
    """

    _ftdi_interface = ConfigOption(
        'ftdi_interface', "ftdi:///1", missing='warn')
    _ccp_header_file = ConfigOption(
        'ccp_header_file',
        r"hardware\diy_daq\MAX11300Hex.h",
        missing='warn')

    def on_activate(self):
        """ Activate module.
        """
        Ftdi.show_devices()

        self.max113xx = MAX113XX(self._ftdi_interface,
                                 self._ccp_header_file)

        is_ok = (DIY_DAQ.max113xx.readRegister(0x00) !=0x000)
        if not is_ok:
            self.log.error("MAX113XX has no power")

    def on_deactivate(self):
        """ Deactivate module.
        """

    def get_process_unit(self, channel=None):
        """ Process unit, here Pa.

            @return float: process unit
        """
        return 'V', 'volts'

    def get_control_unit(self, channel=None):
        """ Get unit of control value.

            @return tuple(str): short and text unit of control value
        """
        return 'V', 'volts'

    def get_control_limit(self, channel=None):
        """ Get minimum and maximum of control value.

            @return tuple(float, float): minimum and maximum of control value
        """
        # FIXME:
        return 0, 10

    def get_minimal_step(self):
        return 1 / self.bin_to_volt(0x001)

    def bin_to_volt(self, val):
        return val / 0xfff * 10

    def volt_to_bin(self, val):
        return int(val / 10 * 0xfff)

    def get_process_value(self, channel=None):
        """ Process value, here temperature.

            @return float: process value
        """
        if channel is not None:
            ret = self.max113xx.readRegister(f'adc_data_port_{channel:02}')
            return self.bin_to_volt(ret)
        else:
            ret = self.max113xx.blockRead(f'adc_data_port_00', 20)
            return [self.bin_to_volt(val) for val in ret]

    def get_control_value(self, channel=None):
        """ Get current control value, here heating power

            @return float: current control value
        """
        if channel is not None:
            ret = self.max113xx.readRegister(f'dac_data_port_{channel:02}')
            return self.bin_to_volt(ret)
        else:
            ret = self.max113xx.blockRead(f'dac_data_port_00', 20)
            return list(map(self.bin_to_volt, ret))

    def set_control_value(self, value, channel=None):
        """ Set control value, here heating power.

            @param float value: control value
        """
        if channel is not None:
            val = self.volt_to_bin(value)
            self.max113xx.writeRegister(f'dac_data_port_{channel:02}', val)
        else:
            val = list(map(self.volt_to_bin, value))
            ret = self.max113xx.blockWrite(f'dac_data_port_00', val)
