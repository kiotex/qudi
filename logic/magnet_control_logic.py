# -*- coding: utf-8 -*-

"""
This file contains the Qudi Logic module base class.

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

from qtpy import QtCore
from collections import OrderedDict
from interface.microwave_interface import MicrowaveMode
from interface.microwave_interface import TriggerEdge
import numpy as np
import time
import datetime
import matplotlib.pyplot as plt
import pyvisa
import lmfit
from core.util.mutex import Mutex

from logic.generic_logic import GenericLogic
from core.util.mutex import Mutex
from core.module import Connector, ConfigOption, StatusVar

class MagnetControlLogic(GenericLogic):

    """This is the Logic class for ODMR."""
    _modclass = 'magnetcontrollogic'
    _modtype = 'logic'

    # declare connectors
    fitlogic = Connector(interface='FitLogic')
    savelogic = Connector(interface='SaveLogic')
    magnetstage = Connector(interface='magnet_control_interface')
    counter = Connector(interface='CounterLogic')

    curr_x_pos = StatusVar('curr_x_pos', 0.0000)
    curr_y_pos = StatusVar('curr_y_pos', 0.0000)
    curr_z_pos = StatusVar('curr_z_pos', 0.0000)

    set_x_pos = StatusVar('set_x_pos', 0.0000)
    set_y_pos = StatusVar('set_y_pos', 0.0000)
    set_z_pos = StatusVar('set_z_pos', 0.0000)

    N_AF_points = StatusVar('N_AF_points', 10)

    x_start = StatusVar('x_start', 9.4600)
    x_end = StatusVar('x_end', 9.9600)
    step_x = StatusVar('step_x', 0.0300)
    n_x_points = StatusVar('n_x_points', 0.0)

    y_start = StatusVar('y_start', 9.4600)
    y_end = StatusVar('y_end', 9.9600)
    step_y = StatusVar('step_y', 0.0300)
    n_y_points = StatusVar('n_y_points', 0.0)

    Xmax = StatusVar('Xmax', 0.0000)
    Ymax = StatusVar('Ymax', 0.0000)

    x_scan_fit_x = StatusVar('x_scan_fit_x', 0.0000)
    x_scan_fit_y = StatusVar('x_scan_fit_x', 0.0000)
    y_scan_fit_x = StatusVar('x_scan_fit_x', 0.0000)
    y_scan_fit_y = StatusVar('x_scan_fit_x', 0.0000)

    fc = StatusVar('fits', None)
    i = StatusVar('i', 0)

    motion_time = StatusVar('motion_time', 0.0000)

    fluorescence_integration_time = StatusVar('fluorescence_integration_time', 0.5)

    # Update signals, e.g. for GUI module
    sigPlotXUpdated = QtCore.Signal(np.ndarray, np.ndarray)
    sigPlotYUpdated = QtCore.Signal(np.ndarray, np.ndarray)
    sigFitXUpdated = QtCore.Signal(np.ndarray, np.ndarray, dict, str)
    sigFitYUpdated = QtCore.Signal(np.ndarray, np.ndarray, dict, str)
    sigPositionUpdated = QtCore.Signal()
    sigNextXPoint = QtCore.Signal()
    sigNextYPoint = QtCore.Signal()
    signal_stop_scanning = QtCore.Signal()

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)
        self.threadlock = Mutex()

    def on_activate(self):
        """
        Initialisation performed during activation of the module.
        """
        # Get connectors
        self._magnetstage = self.get_connector('magnetstage')
        self._fit_logic = self.get_connector('fitlogic')
        self._counter = self.get_connector('counter')
        self._save_logic = self.get_connector('savelogic')

        # Set flags
        # for stopping a measurement
        self.stopRequested = False

        # Initalize the ODMR data arrays (mean signal and sweep matrix)
        self._initialize_plots()

        # Connect signals
        self.sigNextXPoint.connect(self._next_x_point, QtCore.Qt.QueuedConnection)
        self.sigNextYPoint.connect(self._next_y_point, QtCore.Qt.QueuedConnection)

        return

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        return

    @fc.constructor
    def sv_set_fits(self, val):
        # Setup fit container
        fc = self.fitlogic().make_fit_container('length', '1d')
        fc.set_units(['mm', 'c/s'])
        if isinstance(val, dict) and len(val) > 0:
            fc.load_from_dict(val)
        else:
            d1 = OrderedDict()
            d1['Gaussian peak'] = {
                'fit_function': 'gaussian',
                'estimator': 'peak'
            }

            d1['Lorentzian peak'] = {
                'fit_function': 'lorentzian',
                'estimator': 'peak'
            }
            d1['Two Lorentzian dips'] = {
                'fit_function': 'lorentziandouble',
                'estimator': 'dip'
            }
            d1['N14'] = {
                'fit_function': 'lorentziantriple',
                'estimator': 'N14'
            }
            d1['N15'] = {
                'fit_function': 'lorentziandouble',
                'estimator': 'N15'
            }

            default_fits = OrderedDict()
            default_fits['1d'] = d1['Gaussian peak']

            fc.load_from_dict(default_fits)
        return fc

    @fc.representer
    def sv_get_fits(self, val):
        """ save configured fits """
        if len(val.fit_list) > 0:
            return val.save_to_dict()
        else:
            return None

    def _initialize_plots(self):
        """ Initializing the ODMR plots (line and matrix). """
        self.fluor_plot_x = np.arange(self.x_start, self.x_end, self.step_x)
        self.fluor_plot_y = np.zeros(self.fluor_plot_x.size)

        self.x_scan_fit_x = np.arange(self.x_start, self.x_end, self.step_x)
        self.x_scan_fit_y = np.zeros(self.fluor_plot_x.size)

        self.yfluor_plot_x = np.arange(self.y_start, self.y_end, self.step_y)
        self.yfluor_plot_y = np.zeros(self.yfluor_plot_x.size)

        self.y_scan_fit_x = np.arange(self.y_start, self.y_end, self.step_y)
        self.y_scan_fit_y = np.zeros(self.yfluor_plot_x.size)

        self.sigPlotXUpdated.emit(self.fluor_plot_x, self.fluor_plot_y)
        self.sigPlotYUpdated.emit(self.yfluor_plot_x, self.yfluor_plot_y)

        current_x_fit = self.fc.current_fit
        self.sigFitXUpdated.emit(self.x_scan_fit_x, self.x_scan_fit_y, {}, current_x_fit)

        current_y_fit = self.fc.current_fit
        self.sigFitXUpdated.emit(self.y_scan_fit_x, self.y_scan_fit_y, {}, current_y_fit)
        return

    def get_current_position(self):
        try:
            self.curr_x_pos = float(self._magnetstage.get_current_position(1)[3:-2])
        except pyvisa.errors.VisaIOError:
            print('visa error')
            time.sleep(0.05)
            try:
                self.curr_x_pos = float(self._magnetstage.get_current_position(1)[3:-2])
            except pyvisa.errors.VisaIOError:
                print('visa error')
                time.sleep(0.05)
                self.curr_x_pos = float(self._magnetstage.get_current_position(1)[3:-2])

        time.sleep(0.05)
        try:
            self.curr_y_pos = float(self._magnetstage.get_current_position(2)[3:-2])
        except pyvisa.errors.VisaIOError:
            print('visa error')
            time.sleep(0.05)
            self.curr_y_pos = float(self._magnetstage.get_current_position(2)[3:-2])
        self.curr_z_pos = float(self._magnetstage.get_current_position(3)[3:-2])

        return

    def set_position(self):
        self._magnetstage.move_absolute(1, self.set_x_pos)
        self._magnetstage.move_absolute(2, self.set_y_pos)
        self._magnetstage.move_absolute(3, self.set_z_pos)
        return

    def start_x_scanning(self, tag='logic'):
        """Starts scanning
        """
        with self.threadlock:
            if self.module_state() == 'locked':
                self.log.error('Can not start fluorescence scan. Logic is already locked.')

                return -1

            self.module_state.lock()
            self.stopRequested = False

            self.step_x = int(self.step_x/ 2e-4) * 2e-4
            self.fluor_plot_x = np.arange(self.x_start, self.x_end, self.step_x)
            self.fluor_plot_y = np.zeros((len(self.fluor_plot_x)))
            self.curr_x_pos = float(self._magnetstage.get_current_position(1)[3:-2])
            time.sleep(0.1)
            self.motion_time = float(self._magnetstage.get_motiontime_relativemove(1, self.step_x)[3:-2])+0.05

            if self.x_start!=self.curr_x_pos:
                t = float(self._magnetstage.get_motiontime_relativemove(1, np.abs(self.x_start - self.curr_x_pos))[3:-2])
                self._magnetstage.move_absolute(1, self.x_start)
                time.sleep(t + 1)

            self.get_current_position()
            self.i=0
            self.sigNextXPoint.emit()

            return 0

    def _next_x_point(self):

        with self.threadlock:
            # If the odmr measurement is not running do nothing
            if self.module_state() != 'locked':
                return

            # Stop measurement if stop has been requested
            if self.stopRequested:
                self.stopRequested = False
                self._magnetstage.stop_motion(1)
                self.signal_stop_scanning.emit()
                self.module_state.unlock()
                return

            # Move the magnet
            self._magnetstage.move_relative(1, self.step_x)
            time.sleep(self.motion_time)
            self.curr_x_pos = float(self._magnetstage.get_current_position(1)[3:-2])
            time.sleep(0.1)
            if self.curr_x_pos > (self.x_end+self.step_x):
                self.stopRequested = False
                self._magnetstage.stop_motion(1)
                self.module_state.unlock()
                self.signal_stop_scanning.emit()
                return

            # Acquire count data
            if self.i<=(self.n_x_points-1):
                self.fluor_plot_y[self.i] = self._perform_fluorescence_measure()[0]
                self.i=self.i+1

            else:
                self.module_state.unlock()
                self.signal_stop_scanning.emit()
                return


            # Fire update signals
            self.sigPlotXUpdated.emit(self.fluor_plot_x, self.fluor_plot_y)
            self.sigPositionUpdated.emit()
            self.sigNextXPoint.emit()
            return

    def start_y_scanning(self, tag='logic'):
        """Starts scanning
        """
        with self.threadlock:
            if self.module_state() == 'locked':
                self.log.error('Can not start ODMR scan. Logic is already locked.')
                return -1

            self.module_state.lock()
            self.stopRequested = False

            self.step_y = int(self.step_y/ 2e-4) * 2e-4
            self.yfluor_plot_x = np.arange(self.y_start, self.y_end, self.step_y)
            self.yfluor_plot_y = np.zeros((len(self.yfluor_plot_x)))
            self.curr_y_pos = float(self._magnetstage.get_current_position(1)[3:-2])

            time.sleep(0.1)
            self.motion_time = float(self._magnetstage.get_motiontime_relativemove(2, self.step_y)[3:-2])+0.05
            if self.y_start!=self.curr_y_pos:
                t = float(self._magnetstage.get_motiontime_relativemove(2, np.abs(self.y_start - self.curr_y_pos))[3:-2])
                self._magnetstage.move_absolute(2, self.y_start)
                time.sleep(t + 1)

            self.get_current_position()
            self.i=0
            self.sigNextYPoint.emit()

            return 0

    def _next_y_point(self):

        with self.threadlock:
            # If the odmr measurement is not running do nothing
            if self.module_state() != 'locked':
                return

            # Stop measurement if stop has been requested
            if self.stopRequested:
                self.stopRequested = False
                self._magnetstage.stop_motion(2)
                self.signal_stop_scanning.emit()
                self.module_state.unlock()
                return

            # Move the magnet
            self._magnetstage.move_relative(2, self.step_y)
            time.sleep(self.motion_time+0.1)
            self.curr_y_pos = float(self._magnetstage.get_current_position(2)[3:-2])
            time.sleep(0.1)
            if self.curr_y_pos > (self.y_end+self.step_y):
                self.stopRequested = False
                self._magnetstage.stop_motion(2)
                self.module_state.unlock()
                self.signal_stop_scanning.emit()
                return

            # Acquire count data
            if self.i <= (self.n_y_points - 1):
                self.yfluor_plot_y[self.i] = self._perform_fluorescence_measure()[0]
                self.i=self.i+1
            else:
                self.module_state.unlock()
                self.signal_stop_scanning.emit()
                return

            # Fire update signals
            self.sigPlotYUpdated.emit(self.yfluor_plot_x, self.yfluor_plot_y)
            self.sigPositionUpdated.emit()
            self.sigNextYPoint.emit()
            return

    def stop_scanning(self):
        """Stops the scan

        @return int: error code (0:OK, -1:error)
        """
        with self.threadlock:
            if self.module_state() == 'locked':
                self.stopRequested = True
        self.signal_stop_scanning.emit()
        return 0

    def _perform_fluorescence_measure(self):

        #FIXME: that should be run through the TaskRunner! Implement the call
        #       by not using this connection!

        if self._counter.get_counting_mode() != 0:
            self._counter.set_counting_mode(mode='CONTINUOUS')

        self._counter.start_saving()
        time.sleep(self.fluorescence_integration_time)
        self._counter.stopCount()
        data_array, parameters = self._counter.save_data(to_file=False)

        data_array = np.array(data_array)[:, 1]

        return data_array.mean(), parameters

    def get_fit_x_functions(self):
        """ Return the hardware constraints/limits
        @return list(str): list of fit function names
        """
        return list(self.fc.fit_list)

    def get_fit_y_functions(self):
        """ Return the hardware constraints/limits
        @return list(str): list of fit function names
        """
        return list(self.fc.fit_list)

    def do_x_fit(self, fit_function=None, x_data=None, y_data=None):
        """
        Execute the currently configured fit on the measurement data. Optionally on passed data
        """
        if (x_data is None) or (y_data is None):
            x_data = self.fluor_plot_x
            y_data = self.fluor_plot_y

        if fit_function is not None and isinstance(fit_function, str):
            if fit_function in self.get_fit_x_functions():
                self.fc.set_current_fit(fit_function)
            else:
                self.fc.set_current_fit('No Fit')
                if fit_function != 'No Fit':
                    self.log.warning('Fit function "{0}" not available in ODMRLogic fit container.'
                                     ''.format(fit_function))

        self.x_scan_fit_x, self.x_scan_fit_y, result = self.fc.do_fit(x_data, y_data)

        if result is None:
            result_str_dict = {}
        else:
            result_str_dict = result.result_str_dict
        # print(result.result_str_dict)
        self.sigFitXUpdated.emit(self.x_scan_fit_x, self.x_scan_fit_y,
                                    result_str_dict, self.fc.current_fit)
        return

    def do_y_fit(self, fit_function=None, x_data=None, y_data=None):
        """
        Execute the currently configured fit on the measurement data. Optionally on passed data
        """
        if (x_data is None) or (y_data is None):
            x_data = self.yfluor_plot_x
            y_data = self.yfluor_plot_y

        if fit_function is not None and isinstance(fit_function, str):
            if fit_function in self.get_fit_y_functions():
                self.fc.set_current_fit(fit_function)
            else:
                self.fc.set_current_fit('No Fit')
                if fit_function != 'No Fit':
                    self.log.warning('Fit function "{0}" not available in ODMRLogic fit container.'
                                     ''.format(fit_function))

        self.y_scan_fit_x, self.y_scan_fit_y, result = self.fc.do_fit(x_data, y_data)

        if result is None:
            result_str_dict = {}
        else:
            result_str_dict = result.result_str_dict
        self.sigFitYUpdated.emit(self.y_scan_fit_x, self.y_scan_fit_y,
                                    result_str_dict, self.fc.current_fit)
        return

    def save_data(self, tag=None, colorscale_range=None, percentile_range=None):
        """ Saves the current data to a file."""
        if tag is None:
            tag = ''

        # two paths to save the raw data and the odmr scan data.
        filepath = self._save_logic.get_path_for_module(module_name='MAGNET')
        filepath2 = self._save_logic.get_path_for_module(module_name='MAGNET')

        timestamp = datetime.datetime.now()

        if len(tag) > 0:
            filelabel = tag + '_ODMR_data'
            filelabel2 = tag + '_ODMR_data_raw'
        else:
            filelabel = 'ODMR_data'
            filelabel2 = 'ODMR_data_raw'

        # prepare the data in a dict or in an OrderedDict:
        data = OrderedDict()
        data2 = OrderedDict()
        data['frequency (Hz)'] = self.odmr_plot_x
        data['count data (counts/s)'] = self.odmr_plot_y
        data2['count data (counts/s)'] = self.odmr_raw_data[:self.elapsed_sweeps, :]

        parameters = OrderedDict()
        parameters['Microwave CW Power (dBm)'] = self.cw_mw_power
        parameters['Microwave Sweep Power (dBm)'] = self.sweep_mw_power
        parameters['Run Time (s)'] = self.run_time
        parameters['Number of frequency sweeps (#)'] = self.elapsed_sweeps
        parameters['Start Frequency (Hz)'] = self.mw_start
        parameters['Stop Frequency (Hz)'] = self.mw_stop
        parameters['Step size (Hz)'] = self.mw_step
        parameters['Clock Frequency (Hz)'] = self.clock_frequency
        if self.fc.current_fit != 'No Fit':
            parameters['Fit function'] = self.fc.current_fit

        # add all fit parameter to the saved data:
        for name, param in self.fc.current_fit_param.items():
            parameters[name] = str(param)

        fig = self.draw_figure(cbar_range=colorscale_range, percentile_range=percentile_range)

        self._save_logic.save_data(data,
                                   filepath=filepath,
                                   parameters=parameters,
                                   filelabel=filelabel,
                                   fmt='%.6e',
                                   delimiter='\t',
                                   timestamp=timestamp,
                                   plotfig=fig)

        self._save_logic.save_data(data2,
                                   filepath=filepath2,
                                   parameters=parameters,
                                   filelabel=filelabel2,
                                   fmt='%.6e',
                                   delimiter='\t',
                                   timestamp=timestamp)

        self.log.info('ODMR data saved to:\n{0}'.format(filepath))
        return

    def draw_figure(self, cbar_range=None, percentile_range=None):
        """ Draw the summary figure to save with the data.

        @param: list cbar_range: (optional) [color_scale_min, color_scale_max].
                                 If not supplied then a default of data_min to data_max
                                 will be used.

        @param: list percentile_range: (optional) Percentile range of the chosen cbar_range.

        @return: fig fig: a matplotlib figure object to be saved to file.
        """
        freq_data = self.odmr_plot_x
        count_data = self.odmr_plot_y
        fit_freq_vals = self.odmr_fit_x
        fit_count_vals = self.odmr_fit_y
        matrix_data = self.odmr_plot_xy

        # If no colorbar range was given, take full range of data
        if cbar_range is None:
            cbar_range = np.array([np.min(matrix_data), np.max(matrix_data)])
        else:
            cbar_range = np.array(cbar_range)

        prefix = ['', 'k', 'M', 'G', 'T']
        prefix_index = 0

        # Rescale counts data with SI prefix
        while np.max(count_data) > 1000:
            count_data = count_data / 1000
            fit_count_vals = fit_count_vals / 1000
            prefix_index = prefix_index + 1

        counts_prefix = prefix[prefix_index]

        # Rescale frequency data with SI prefix
        prefix_index = 0

        while np.max(freq_data) > 1000:
            freq_data = freq_data / 1000
            fit_freq_vals = fit_freq_vals / 1000
            prefix_index = prefix_index + 1

        mw_prefix = prefix[prefix_index]

        # Rescale matrix counts data with SI prefix
        prefix_index = 0

        while np.max(matrix_data) > 1000:
            matrix_data = matrix_data / 1000
            cbar_range = cbar_range / 1000
            prefix_index = prefix_index + 1

        cbar_prefix = prefix[prefix_index]

        # Use qudi style
        plt.style.use(self._save_logic.mpl_qd_style)

        # Create figure
        fig, (ax_mean, ax_matrix) = plt.subplots(nrows=2, ncols=1)

        ax_mean.plot(freq_data, count_data, linestyle=':', linewidth=0.5)

        # Do not include fit curve if there is no fit calculated.
        if max(fit_count_vals) > 0:
            ax_mean.plot(fit_freq_vals, fit_count_vals, marker='None')

        ax_mean.set_ylabel('Fluorescence (' + counts_prefix + 'c/s)')
        ax_mean.set_xlim(np.min(freq_data), np.max(freq_data))

        matrixplot = ax_matrix.imshow(matrix_data,
                                      cmap=plt.get_cmap('inferno'),  # reference the right place in qd
                                      origin='lower',
                                      vmin=cbar_range[0],
                                      vmax=cbar_range[1],
                                      extent=[np.min(freq_data),
                                              np.max(freq_data),
                                              0,
                                              self.number_of_lines
                                              ],
                                      aspect='auto',
                                      interpolation='nearest')

        ax_matrix.set_xlabel('Frequency (' + mw_prefix + 'Hz)')
        ax_matrix.set_ylabel('Scan #')

        # Adjust subplots to make room for colorbar
        fig.subplots_adjust(right=0.8)

        # Add colorbar axis to figure
        cbar_ax = fig.add_axes([0.85, 0.15, 0.02, 0.7])

        # Draw colorbar
        cbar = fig.colorbar(matrixplot, cax=cbar_ax)
        cbar.set_label('Fluorescence (' + cbar_prefix + 'c/s)')

        # remove ticks from colorbar for cleaner image
        cbar.ax.tick_params(which=u'both', length=0)

        # If we have percentile information, draw that to the figure
        if percentile_range is not None:
            cbar.ax.annotate(str(percentile_range[0]),
                             xy=(-0.3, 0.0),
                             xycoords='axes fraction',
                             horizontalalignment='right',
                             verticalalignment='center',
                             rotation=90
                             )
            cbar.ax.annotate(str(percentile_range[1]),
                             xy=(-0.3, 1.0),
                             xycoords='axes fraction',
                             horizontalalignment='right',
                             verticalalignment='center',
                             rotation=90
                             )
            cbar.ax.annotate('(percentile)',
                             xy=(-0.3, 0.5),
                             xycoords='axes fraction',
                             horizontalalignment='right',
                             verticalalignment='center',
                             rotation=90
                             )

        return fig