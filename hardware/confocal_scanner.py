# -*- coding: utf-8 -*-
"""
This file contains the Qudi dummy module for the confocal scanner.

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
import time

from core.module import Base, Connector, ConfigOption
from interface.confocal_scanner_interface import ConfocalScannerInterface


class ConfocalScanner(Base, ConfocalScannerInterface):

    _modclass = 'ConfocalScanner'
    _modtype = 'hardware'

    # connectors
    fitlogic = Connector(interface='FitLogic')

    # config
    _clock_frequency = ConfigOption('clock_frequency', 100, missing='warn')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        # Internal parameters
        self._line_length = None
        self._voltage_range = [0, 10]

        self._position_range = [[0, 50e-6], [0, 50e-6], [-25e-6, 25e-6], [0, 1e-6]]
        self._current_position = [0, 0, 0, 0][0:len(self.get_scanner_axes())]
        self._num_points = 500

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._fit_logic = self.get_connector('fitlogic')

    def on_deactivate(self):
        """ Deactivate properly the confocal scanner dummy.
        """
        self.reset_hardware()

    def reset_hardware(self):
        """ Resets the hardware, so the connection is lost and other programs
            can access it.

        @return int: error code (0:OK, -1:error)
        """
        self.log.warning('Scanning Device will be reset.')
        return 0

    def get_position_range(self):
        """ Returns the physical range of the scanner.

        @return float [4][2]: array of 4 ranges with an array containing lower
                              and upper limit
        """
        return self._position_range

    def set_position_range(self, myrange=None):
        """ Sets the physical range of the scanner.

        @param float [4][2] myrange: array of 4 ranges with an array containing
                                     lower and upper limit

        @return int: error code (0:OK, -1:error)
        """
        if myrange is None:
            myrange = [[0, 1e-6], [0, 1e-6], [0, 1e-6], [0, 1e-6]]

        if not isinstance(myrange, (frozenset, list, set, tuple, np.ndarray, )):
            self.log.error('Given range is no array type.')
            return -1

        if len(myrange) != 4:
            self.log.error('Given range should have dimension 4, but has '
                    '{0:d} instead.'.format(len(myrange)))
            return -1

        for pos in myrange:
            if len(pos) != 2:
                self.log.error('Given range limit {1:d} should have '
                        'dimension 2, but has {0:d} instead.'.format(
                            len(pos),
                            pos))
                return -1
            if pos[0]>pos[1]:
                self.log.error('Given range limit {0:d} has the wrong '
                        'order.'.format(pos))
                return -1

        self._position_range = myrange

        return 0

    def set_voltage_range(self, myrange=None):
        """ Sets the voltage range of the NI Card.

        @param float [2] myrange: array containing lower and upper limit

        @return int: error code (0:OK, -1:error)
        """
        if myrange is None:
            myrange = [0.,10.]

        if not isinstance(myrange, (frozenset, list, set, tuple, np.ndarray, )):
            self.log.error('Given range is no array type.')
            return -1

        if len(myrange) != 2:
            self.log.error('Given range should have dimension 2, but has '
                    '{0:d} instead.'.format(len(myrange)))
            return -1

        if myrange[0]>myrange[1]:
            self.log.error('Given range limit {0:d} has the wrong '
                    'order.'.format(myrange))
            return -1

        if self.getState() == 'locked':
            self.log.error('A Scanner is already running, close this one '
                    'first.')
            return -1

        self._voltage_range = myrange

        return 0

    def get_scanner_axes(self):
        """ Dummy scanner is always 3D cartesian.
        """
        return ['x', 'y', 'z', 'a']

    def get_scanner_count_channels(self):
        """ 3 counting channels in dummy confocal: normal, negative and a ramp."""
        return ['Norm', 'Neg', 'Ramp']

    def set_up_scanner_clock(self, clock_frequency=None, clock_channel=None):
        """ Configures the hardware clock of the NiDAQ card to give the timing.

        @param float clock_frequency: if defined, this sets the frequency of the
                                      clock
        @param str clock_channel: if defined, this is the physical channel of
                                  the clock

        @return int: error code (0:OK, -1:error)
        """

        if clock_frequency is not None:
            self._clock_frequency = float(clock_frequency)

        self.log.debug('ConfocalScanner>set_up_scanner_clock')
        time.sleep(0.2)
        return 0


    def set_up_scanner(self, counter_channels=None, sources=None,
                       clock_channel=None, scanner_ao_channels=None):
        """ Configures the actual scanner with a given clock.

        @param str counter_channel: if defined, this is the physical channel of
                                    the counter
        @param str photon_source: if defined, this is the physical channel where
                                  the photons are to count from
        @param str clock_channel: if defined, this specifies the clock for the
                                  counter
        @param str scanner_ao_channels: if defined, this specifies the analoque
                                        output channels

        @return int: error code (0:OK, -1:error)
        """

        self.log.debug('ConfocalScannerDummy>set_up_scanner')
        time.sleep(0.2)
        return 0


    def scanner_set_position(self, x=None, y=None, z=None, a=None):
        """Move stage to x, y, z, a (where a is the fourth voltage channel).

        @param float x: postion in x-direction (volts)
        @param float y: postion in y-direction (volts)
        @param float z: postion in z-direction (volts)
        @param float a: postion in a-direction (volts)

        @return int: error code (0:OK, -1:error)
        """

        if self.getState() == 'locked':
            self.log.error('A Scanner is already running, close this one first.')
            return -1

        time.sleep(0.01)

        self._current_position = [x, y, z, a][0:len(self.get_scanner_axes())]
        return 0

    def get_scanner_position(self):
        """ Get the current position of the scanner hardware.

        @return float[]: current position in (x, y, z, a).
        """
        return self._current_position[0:len(self.get_scanner_axes())]

    def _set_up_line(self, length=100):
        """ Sets up the analoque output for scanning a line.

        @param int length: length of the line in pixel

        @return int: error code (0:OK, -1:error)
        """

        self._line_length = length

#        self.log.debug('ConfocalScannerInterfaceDummy>set_up_line')
        return 0

    def scan_line(self, line_path=None, pixel_clock=False):
        """ Scans a line and returns the counts on that line.

        @param float[][4] line_path: array of 4-part tuples defining the voltage points
        @param bool pixel_clock: whether we need to output a pixel clock for this line

        @return float[]: the photon counts per second
        """

        if not isinstance(line_path, (frozenset, list, set, tuple, np.ndarray, )):
            self.log.error('Given voltage list is no array type.')
            return np.array([[-1.]])

        if np.shape(line_path)[1] != self._line_length:
            self._set_up_line(np.shape(line_path)[1])

        count_data = np.zeros(self._line_length)
        z_data = line_path[2, :]

        #the gaussian functions
        x_data = np.array(line_path[0, :])
        y_data = np.array(line_path[1, :])
        for i in range(self._num_points):
            count_data += x_data

        time.sleep(self._line_length * 1. / self._clock_frequency)
        time.sleep(self._line_length * 1. / self._clock_frequency)

        # update the scanner position instance variable
        self._current_position = list(line_path[:, -1])

        return np.array([
                count_data,
                5e5 - count_data,
                np.ones(count_data.shape) * line_path[1, 0] * 100
            ]).transpose()

        print(x_data)

        return self._scan_line()

    def close_scanner(self):
        """ Closes the scanner and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """

        self.log.debug('ConfocalScannerDummy>close_scanner')
        return 0

    def close_scanner_clock(self, power=0):
        """ Closes the clock and cleans up afterwards.

        @return int: error code (0:OK, -1:error)
        """

        self.log.debug('ConfocalScannerDummy>close_scanner_clock')
        return 0