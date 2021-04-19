# -*- coding: utf-8 -*-

"""
This file contains the Qudi interfuse between a process control and a process control.
---

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
from enum import Enum

from core.connector import Connector
from core.configoption import ConfigOption
from core.statusvariable import StatusVar
from logic.generic_logic import GenericLogic

from interface.process_control_interface import ProcessControlInterface
from interface.process_interface import ProcessInterface

from interface.simple_data_interface import SimpleDataInterface

from interface.slow_counter_interface import SlowCounterInterface
from interface.slow_counter_interface import SlowCounterConstraints
from interface.slow_counter_interface import CountingMode


class ProcessMode(Enum):
    Control = "ProcessControlInterface"
    Process = "ProcessInterface"


class ProcessInterfaceAdapter(
        GenericLogic,
        ProcessInterface,
        ProcessControlInterface,
        SimpleDataInterface,
        SlowCounterInterface):
    """ This interfuse can be used to modify a process control on the fly. It needs a 2D array to interpolate

    TODO: docstringを書き直す

    """

    _control = Connector(interface='ProcessControlInterface', optional=True)
    _process = Connector(interface='ProcessInterface', optional=True)

    def on_activate(self):
        """ Activate module.
        """

        if self._control.is_connected:
            self.hardware = self._control()
            self.mode = ProcessMode.Control
            if self._process.is_connected:
                self.log.warn("This interfuse accepts only one interface")
        elif self._process.is_connected:
            self.hardware = self._process()
        else:
            self.log.error("No process interface is assigned")

    def on_deactivate(self):
        """ Deactivate module.
        """
        pass

    # ================ ProcessInterface Commands =======================
    def get_process_value(self, channel=None):
        """ Return a measured value

        @param (int) channel: (Optional) The number of the channel
        @return (float): The measured process value
        """
        return self.hardware.get_process_value(channel)

    def get_process_value_maximum(self):
        """ Return a measured value

        @param (int) channel: (Optional) The number of the channel
        @return (float): The measured process value
        """
        return self.hardware.get_process_value_maximum()

    def get_process_unit(self, channel=None):
        """ Return the unit that the value is measured in as a tuple of ('abbreviation', 'full unit name')

        @param (int) channel: (Optional) The number of the channel

        @return: The unit as a tuple of ('abbreviation', 'full unit name')

         """
        return self.hardware.get_process_unit(channel)

    def process_supports_multiple_channels(self):
        """ Function to test if hardware support multiple channels

        @return (bool): Whether the hardware supports multiple channels

        This function is not abstract - Thus it is optional and if a hardware do not implement it, the answer is False.
        """
        return self.hardware.process_supports_multiple_channels()

    def process_get_number_channels(self):
        """ Function to get the number of channels available for measure

        @return (int): The number of channel(s)

        This function is not abstract - Thus it is optional and if a hardware do not implement it, the answer is 1.
        """
        return self.hardware.process_get_number_channels()

    # ================ End ProcessInterface Commands =======================

    # ================ ProcessControlInterface Commands =======================

    def set_control_value(self, value, channel=None):
        """ Set the value of the controlled process variable

        @param (float) value: The value to set
        @param (int) channel: (Optional) The number of the channel

        """
        return self.hardware.set_control_value(channel)

    def get_control_value(self, channel=None):
        """ Get the value of the controlled process variable

        @param (int) channel: (Optional) The number of the channel

        @return (float): The current control value
        """
        return self.hardware.get_control_value(channel)

    def get_control_unit(self, channel=None):
        """ Return the unit that the value is set in as a tuple of ('abbreviation', 'full unit name')

        @param (int) channel: (Optional) The number of the channel

        @return: The unit as a tuple of ('abbreviation', 'full unit name')
        """
        return self.hardware.get_control_unit(channel)

    def get_control_limit(self, channel=None):
        """ Return limits within which the controlled value can be set as a tuple of (low limit, high limit)

        @param (int) channel: (Optional) The number of the channel

        @return (tuple): The limits as (low limit, high limit)
        """
        return self.hardware.get_control_limit(channel)

    def process_control_supports_multiple_channels(self):
        """ Function to test if hardware support multiple channels

        @return (bool): Whether the hardware supports multiple channels

        This function is not abstract - Thus it is optional and if a hardware do not implement it, the answer is False.
        """
        return self.hardware.process_control_supports_multiple_channels()

    def process_control_get_number_channels(self):
        """ Function to get the number of channels available for control

        @return (int): The number of controllable channel(s)

        This function is not abstract - Thus it is optional and if a hardware do not implement it, the answer is 1.
        """
        return self.hardware.process_control_get_number_channels()

    # ================ End ProcessControlInterface Commands ==================

    # ================ SlowCounterInterface Commands =======================

    def get_constraints(self):
        """ Retrieve the hardware constrains from the counter device.

        @return (SlowCounterConstraints): object with constraints for the counter
        """
        constraints = SlowCounterConstraints()
        constraints.min_count_frequency = 5e-5
        constraints.max_count_frequency = 5e5
        constraints.counting_mode = [
            CountingMode.CONTINUOUS,
            CountingMode.GATED,
            CountingMode.FINITE_GATED]

        return constraints

    def get_counter(self, samples=1):
        """ Returns the current counts per second of the counter.

        @param int samples: if defined, number of samples to read in one go

        @return numpy.array((n, uint32)): the measured quantity of each channel
        """
        if hasattr(self.hardware, "get_counter"):
            return self.hardware.get_counter()

        ret = list()

        if hasattr(self.hardware, "get_process_value"):
            ret += [[self.get_process_value(channel=i)]
                    for i in range(self.process_get_number_channels())]

        if hasattr(self.hardware, "get_control_value"):
            ret += [[self.get_control_value(channel=i)]
                    for i in range(self.process_control_get_number_channels())]

        return np.array(ret)

    def get_counter_channels(self):
        """ Returns the list of counter channel names.

        @return list(str): channel names

        Most methods calling this might just care about the number of channels, though.
        """
        if hasattr(self.hardware, "get_counter_channels"):
            return self.hardware.get_counter_channels()

        ret = list()

        if hasattr(self.hardware, "get_process_value"):
            ret += [f'PV_{i}'
                    for i in range(self.process_get_number_channels())]

        if hasattr(self.hardware, "get_control_value"):
            ret += [f'SV_{i}'
                    for i in range(self.process_control_get_number_channels())]

        return ret

    def set_up_clock(self, clock_frequency=None, clock_channel=None):
        """ Set the frequency of the counter by configuring the hardware clock

        @param (float) clock_frequency: if defined, this sets the frequency of the clock
        @param (string) clock_channel: if defined, this is the physical channel of the clock
        @return int: error code (0:OK, -1:error)

        TODO: Should the logic know about the different clock channels ?
        """
        return 0

    def set_up_counter(self,
                       counter_channels=None,
                       sources=None,
                       clock_channel=None,
                       counter_buffer=None):
        """ Configures the actual counter with a given clock.

        @param list(str) counter_channels: optional, physical channel of the counter
        @param list(str) sources: optional, physical channel where the photons
                                   photons are to count from
        @param str clock_channel: optional, specifies the clock channel for the
                                  counter
        @param int counter_buffer: optional, a buffer of specified integer
                                   length, where in each bin the count numbers
                                   are saved.

        @return int: error code (0:OK, -1:error)

        There need to be exactly the same number sof sources and counter channels and
        they need to be given in the same order.
        All counter channels share the same clock.
        """
        return 0

    def close_counter(self):
        """ Closes the counter and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        return 0

    def close_clock(self):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)

        TODO: This method is very hardware specific, it should be deprecated
        """
        return 0

    # ================ End SlowCounterInterface Commands =====================

    # ================ SimpleDataInterface Commands =======================

    def getData(self):
        """ Return a measured value

        logic側がfloat型で受け付ける形になっているため、PV(優先), SVの片方を帰す
        """
        if hasattr(self.hardware, "get_process_value"):
            return self.get_process_value(channel=0)
        else:
            return self.get_control_value(channel=0)

    def getChannels(self):
        """ Return number of channels for value """
        return 1

    # ================ End SimpleDataInterface Commands ==================
