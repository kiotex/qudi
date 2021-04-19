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

from core.connector import Connector
from core.configoption import ConfigOption
from core.statusvariable import StatusVar
from logic.generic_logic import GenericLogic


from interface.slow_counter_interface import SlowCounterInterface


class CounterCombinerInterfuse(
        GenericLogic,
        SlowCounterInterface):
    """ This interfuse can be used to modify a process control on the fly. It needs a 2D array to interpolate

    TODO: docstringを書き直す

    """

    _counter0 = Connector(interface='SlowCounterInterface')
    _counter1 = Connector(interface='SlowCounterInterface', optional=True)
    _counter2 = Connector(interface='SlowCounterInterface', optional=True)
    _counter3 = Connector(interface='SlowCounterInterface', optional=True)
    #_counters = [_counter0, _counter1, _counter2, _counter3]

    def on_activate(self):
        """ Activate module.
        """
        self.counters = list()
        """for _counter in self._counters:
            if _counter.is_connected:
                self.counters.append(_counter())"""
        for i in range(4):
            _counter = getattr(self, f"_counter{i}")
            if _counter.is_connected:
                self.counters.append(_counter())

    def on_deactivate(self):
        """ Deactivate module.
        """
        pass

    def get_counter(self, samples=1):
        """ Returns the current counts per second of the counter.

        @param int samples: if defined, number of samples to read in one go

        @return numpy.array((n, uint32)): the measured quantity of each channel
        """
        ret = self.counters[0].get_counter(samples)

        for i in range(1, len(self.counters)):
            ret = np.vstack((ret, self.counters[i].get_counter(samples)))

        return ret

    def get_counter_channels(self):
        """ Returns the list of counter channel names.

        @return list(str): channel names

        Most methods calling this might just care about the number of channels, though.
        """
        ret = list()

        for counter in self.counters:
            ret += counter.get_counter_channels()

        return ret

    def get_constraints(self):
        """ Retrieve the hardware constrains from the counter device.

        @return (SlowCounterConstraints): object with constraints for the counter
        """
        return self.counters[0].get_constraints()

    def set_up_clock(self, clock_frequency=None, clock_channel=None):
        """ Set the frequency of the counter by configuring the hardware clock

        @param (float) clock_frequency: if defined, this sets the frequency of the clock
        @param (string) clock_channel: if defined, this is the physical channel of the clock
        @return int: error code (0:OK, -1:error)

        TODO: Should the logic know about the different clock channels ?
        """
        return self.counters[0].set_up_clock(clock_frequency, clock_channel)

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
        return self.counters[0].set_up_counter(counter_channels,
                                               sources,
                                               clock_channel,
                                               counter_buffer)

    def close_counter(self):
        """ Closes the counter and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """
        return self.counters[0].close_counter()

    def close_clock(self):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)

        TODO: This method is very hardware specific, it should be deprecated
        """
        return self.counters[0].close_clock()
