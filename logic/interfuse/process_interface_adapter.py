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

from interface.data_instream_interface import DataInStreamInterface, DataInStreamConstraints
from interface.data_instream_interface import StreamingMode, StreamChannelType, StreamChannel


class ProcessMode(Enum):
    Control = "ProcessControlInterface"
    Process = "ProcessInterface"


class InterfaceMode(Enum):
    DataInStream = "DataInStreamInterface"
    SlowCounter = "SlowCounterInterface"


class MixedConstraints(SlowCounterConstraints, DataInStreamConstraints):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._digital_channels = digital_channels
        self._analog_channels = analog_channels

        # ==== SlowCounterConstraints ====
        # from slow_counter_dummy
        self.min_count_frequency = 5e-5
        self.max_count_frequency = 5e5
        self.counting_mode = [
            CountingMode.CONTINUOUS,
            CountingMode.GATED,
            CountingMode.FINITE_GATED]
        # ==== End SlowCounterConstraints ====

        # ==== DataInStreamConstraints ====
        # from data_instream_dummy
        self.analog_sample_rate.min = 1
        self.analog_sample_rate.max = 2**31 - 1
        self.analog_sample_rate.step = 1
        self.analog_sample_rate.unit = 'Hz'
        self.digital_sample_rate.min = 1
        self.digital_sample_rate.max = 2**31 - 1
        self.digital_sample_rate.step = 1
        self.digital_sample_rate.unit = 'Hz'
        self.combined_sample_rate = self.analog_sample_rate

        self.read_block_size.min = 1
        self.read_block_size.max = 1000000
        self.read_block_size.step = 1

        # TODO: Implement FINITE streaming mode
        self.streaming_modes = (
            StreamingMode.CONTINUOUS,
        )  # , StreamingMode.FINITE)
        self.data_type = np.float64
        self.allow_circular_buffer = True
        # ==== End DataInStreamConstraints ====

    def copy(self):
        return MixedConstraints(**vars(self))


class ProcessInterfaceAdapter(
        GenericLogic,
        ProcessInterface,
        ProcessControlInterface,
        SimpleDataInterface,
        SlowCounterInterface,
        # DataInStreamInterface
):
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

        self._init_constraints()

    def on_deactivate(self):
        """ Deactivate module.
        """
        pass

    def _init_constraints(self):
        self._constraints = MixedConstraints()

        self.analog_channels = list()
        self.analog_units = list()

        if hasattr(self.hardware, "get_counter_channels"):
            self.analog_channels = self.hardware.get_counter_channels()
            if hasattr(self.hardware, "get_counter_units"):
                self.analog_units = self.hardware.get_counter_units()
            elif hasattr(self.hardware, "get_units"):
                self.analog_units = self.hardware.get_units()
            else:
                if hasattr(self.hardware, "get_process_unit"):
                    unit, _ = self.hardware.get_process_unit()
                    self.analog_units, _ = [unit] * len(self.analog_channels)
                elif hasattr(self.hardware, "get_control_unit"):
                    unit, _ = self.hardware.get_control_unit()
                    self.analog_units, _ = [unit] * len(self.analog_channels)
                else:
                    self.analog_units, _ = [
                        "Unknown unit"] * len(self.analog_channels)

        else:
            if hasattr(self.hardware, "get_process_value"):
                self.analog_channels += [
                    f'PV_{i}' for i in range(
                        self.process_get_number_channels())]
                unit, _ = self.hardware.get_process_unit()
                self.analog_units, _ = [unit] * \
                    self.process_get_number_channels()

            if hasattr(self.hardware, "get_control_value"):
                self.analog_channels += [
                    f'SV_{i}' for i in range(
                        self.process_control_get_number_channels())]
                unit, _ = self.hardware.get_control_unit()
                self.analog_units, _ = [unit] * \
                    self.process_control_get_number_channels()

        self._constraints.analog_channels = tuple(
            StreamChannel(
                name=ch, type=StreamChannelType.ANALOG, unit=unit) for ch, unit in zip(
                self.analog_channels, self.analog_units))

    def get_constraints(self):
        """ Return the constraints on the settings for this hardware.

        @return (MixedConstraints): Instance of MixedConstraints containing constraints
        """
        return self._constraints.copy()

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
        return self.analog_channels

    def set_up_clock(self, clock_frequency=None, clock_channel=None):
        """ Set the frequency of the counter by configuring the hardware clock

        @param (float) clock_frequency: if defined, this sets the frequency of the clock
        @param (string) clock_channel: if defined, this is the physical channel of the clock
        @return int: error code (0:OK, -1:error)
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
        """
        return 0

    # ================ End SlowCounterInterface Commands =====================

    # ================ SimpleDataInterface Commands =======================

    def getData(self):
        """ Return a measured value

        NOTE: logic側がfloat型で受け付ける形になっているため、PV(優先), SVの片方を帰す
        """
        if hasattr(self.hardware, "get_process_value"):
            return self.get_process_value(channel=0)
        else:
            return self.get_control_value(channel=0)

    def getChannels(self):
        """ Return number of channels for value """
        return 1

    # ================ End SimpleDataInterface Commands ==================

    # ================ DataInStreamInterface Commands =======================

    def read_data(self, number_of_samples=1):
        """
        Read data from the stream buffer into a 2D numpy array and return it.
        The arrays first index corresponds to the channel number and the second index serves as
        sample index:
            return_array.shape == (self.number_of_channels, number_of_samples)
        The numpy arrays data type is the one defined in self.data_type.
        If number_of_samples is omitted all currently available samples are read from buffer.

        This method will not return until all requested samples have been read or a timeout occurs.

        If no samples are available, this method will immediately return an empty array.
        You can check for a failed data read if number_of_samples != <return_array>.shape[1].

        @param int number_of_samples: optional, number of samples to read per channel. If omitted, all available samples are read from buffer.

        @return numpy.ndarray: The read samples in a numpy array
        """
        return self.get_counter(number_of_samples)

    def read_single_point(self):
        """
        This method will initiate a single sample read on each configured data channel.
        In general this sample may not be acquired simultaneous for all channels and timing in
        general can not be assured. Us this method if you want to have a non-timing-critical
        snapshot of your current data channel input.
        May not be available for all devices.
        The returned 1D numpy array will contain one sample for each channel.

        @return numpy.ndarray: 1D array containing one sample for each channel. Empty array
                               indicates error.
        """
        return self.get_counter(1).transpose()[0]

    # ================ End DataInStreamInterface Commands =====================
