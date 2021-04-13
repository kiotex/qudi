# -*- coding: utf-8 -*-
"""
This file contains the Qudi hardware dummy for slow counting devices.

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

import numpy as np
import visa

from core.module import Base
from core.configoption import ConfigOption
from interface.process_interface import ProcessInterface
from interface.process_control_interface import ProcessControlInterface


class Agilent3441XA(Base, ProcessInterface, ProcessControlInterface):
    """ Hardware control file for Agilent Devices.

    The hardware file was tested using the model Agilent 34410A.

    Agilent34410A:
        module.Class: 'agilent3441XA.Agilent3441XA'
        usb_address: 'USB0::0x0957::0x0607::my47019114::0::INSTR'
        usb_timeout: 100 # in seconds
        measurement_mode: 'dc_current' #'dc_voltage'
    """

    # config

    _usb_address = ConfigOption('usb_address', missing='error')
    _usb_timeout = ConfigOption('usb_timeout', 100, missing='warn')
    _measurement_mode = ConfigOption('measurement_mode', missing='error')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Initialization performed during activation of the module.
        """
        try:
            # trying to load the visa connection to the module
            self.rm = visa.ResourceManager()
            self._usb_connection = self.rm.open_resource(
                resource_name=self._usb_address,
                timeout=self._usb_timeout)

            IDN = self._usb_connection.query('*IDN?').split(',')
            self.model = IDN[1]
            self.log.info(
                'Agilent3441XA> {0} {1} initialized and connected to hardware.'.format(
                    IDN[0], IDN[1]))

        except BaseException:
            self.log.error(
                'Agilent3441XA> This agilent DMM could not connect to the GPIB '
                'address >>{}<<.'.format(
                    self._usb_address))

        if self._measurement_mode == 'dc_current':
            self._usb_connection.query('MEAS:CURR:DC? AUTO,MAX')
            self.unit = 'A'
            self.unit_name = 'Ampere'
        elif self._measurement_mode == 'dc_voltage':
            self._usb_connection.query('MEAS:DC? AUTO,MAX')
            self.unit = 'V'
            self.unit_name = 'Volt'

    def on_deactivate(self):
        """ De-initialization performed during deactivation of the module.
        """
        self._usb_connection.close()
        self.rm.close()
        self.log.info('Agilent3441XA> deactivation')
        return

    def get_process_unit(self):
        """ Process unit, here Pa.

            @return float: process unit
        """
        return self.unit, self.unit_name

    def get_control_unit(self):
        """ Get unit of control value.

            @return tuple(str): short and text unit of control value
        """
        return self.unit, self.unit_name

    def get_control_limit(self):
        """ Get minimum and maximum of control value.

            @return tuple(float, float): minimum and maximum of control value
        """
        return 0, 1e4

    def get_minimal_step(self):
        return 100.0

    def get_process_value(self):
        """ Process value, here temperature.

            @return float: process value
        """
        return self._usb_connection.query('READ?')

    def get_control_value(self):
        """ Get current control value, here heating power

            @return float: current control value
        """
        return 0

    def set_control_value(self, value):
        return 0

    def get_counter(self, samples=1):
        """ Returns the current counts per second of the counter.

        @param int samples: if defined, number of samples to read in one go

        @return float: the photon counts per second
        """
        return np.array([self._usb_connection.query('READ?')
                         for i in range(samples)])

    def get_counter_channels(self):
        """ Returns the list of counter channel names.
        @return tuple(str): channel names
        Most methods calling this might just care about the number of channels, though.
        """
        return self._measurement_mode
