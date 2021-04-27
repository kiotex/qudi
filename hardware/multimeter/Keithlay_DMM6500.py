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
from hardware.multimeter.Keithley_DMM6500_VISA_Driver import DMM6500

from core.module import Base
from core.configoption import ConfigOption
from interface.process_interface import ProcessInterface


class Keithlay_DMM6500(
        Base,
        ProcessInterface):
    """ Hardware control file for Keithlay DMM6500 Devices.

    The hardware file was tested using the model Keithlay DMM6500.

    Keithlay_DMM6500:
        module.Class: 'multimeter.Keithlay_DMM6500.Keithlay_DMM6500'
        visa_address: 'USB0::0x05E6::0x6500::04464881::INSTR'
        visa_timeout: 100 # in seconds
        measurement_mode: 'dc_current' #'dc_voltage'
    """

    # config

    _visa_address = ConfigOption('visa_address', missing='error')
    _visa_timeout = ConfigOption('visa_timeout', 100, missing='warn')
    _measurement_mode = ConfigOption('measurement_mode', missing='error')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Initialization performed during activation of the module.
        """
        self.dmm6500 = DMM6500()
        try:
            # trying to load the visa connection to the module
            self.rm = visa.ResourceManager()
            self.dmm6500.myInstr = self.rm.open_resource(
                resource_name=self._visa_address,
                timeout=self._visa_timeout)

            # DEBUG: ここでエラー出るかも
            # FIXME:
            IDN = self.dmm6500.IDQuery().split(',')
            self.model = IDN[1]
            self.log.info(
                'Keithlay_DMM6500> {0} {1} initialized and connected to hardware.'.format(
                    IDN[0], IDN[1]))

        except BaseException:
            self.log.error(
                'Keithlay_DMM6500> This agilent DMM could not connect to the GPIB '
                'address >>{}<<.'.format(
                    self._visa_address))

        if self._measurement_mode == 'dc_current':
            self.dmm6500.SetMeasure_Function(self.dmm6500.MeasFunc.DCI)
            # FIXME: レンジ等の設定を書く
            self.unit = 'A'
            self.unit_name = 'Ampere'
        elif self._measurement_mode == 'dc_voltage':
            self.dmm6500.SetMeasure_Function(self.dmm6500.MeasFunc.DCV)
            # FIXME: レンジ等の設定を書く
            self.unit = 'V'
            self.unit_name = 'Volt'

    def on_deactivate(self):
        """ De-initialization performed during deactivation of the module.
        """
        self.dmm6500.Disconnect()
        self.rm.close()
        self.log.info('Keithlay_DMM6500> deactivation')
        return

    # ================ ProcessInterface Commands =======================
    def get_process_unit(self, channel=None):
        """ Get unit of process unit.

            @return tuple(str): short and text unit of control value
        """
        return self.unit, self.unit_name

    def get_process_value(self, channel=None):
        """ Process value, here temperature.

            @return float: process value
        """
        return float(self.dmm6500.Measure(1))
    # ================ End ProcessInterface Commands ==================

    # ================ For SlowCounterInterface Commands =====================
    def get_counter_channels(self):
        """ Returns the list of counter channel names.
        @return tuple(str): channel names
        Most methods calling this might just care about the number of channels, though.
        """
        return self._measurement_mode
    # ================ End SlowCounterInterface Commands ==================
