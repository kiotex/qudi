# -*- coding: utf-8 -*-

"""
This file contains the Qudi GUI for Magnet control.

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
import os
import pyqtgraph as pg
import time

from core.module import Connector, ConfigOption, StatusVar
from gui.guibase import GUIBase
from collections import OrderedDict
from gui.guiutils import ColorBar
from gui.colordefs import ColorScaleInferno
from gui.colordefs import ColorScaleViridis
from gui.colordefs import QudiPalettePale as palette
from gui.fitsettings import FitParametersWidget
from gui.fitsettings import FitSettingsDialog, FitSettingsComboBox
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from core.util import units

class App(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 file dialogs - pythonspot.com'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480

class NVdepthMainWindow(QtWidgets.QMainWindow):

    """ Create the Mainwindow based on the corresponding *.ui file. """

    sigPressKeyBoard = QtCore.Signal(QtCore.QEvent)

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'noise_spectrum.ui')

        # Load it
        super(NVdepthMainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()

class NoiseSpectrumGui(GUIBase):

    """ Class for the alignment of the magnetic field.
    """
    _modclass = 'MagnetControlGui'
    _modtype = 'gui'

    # declare connectors
    fitlogic = Connector(interface='FitLogic')
    savelogic = Connector(interface='SaveLogic')

    fc = StatusVar('fits', None)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Initializes all needed UI files and establishes the connectors.

        This method executes the all the inits for the differnt GUIs and passes
        the event argument from fysom to the methods.
        """

        # # Getting an access to all connectors:
        self._save_logic = self.get_connector('savelogic')
        self._fit_logic = self.get_connector('fitlogic')

        self.initMainUI()      # initialize the main GUI

        self.ex = App()
        self.initAppUI()

        self._mw.actionOpen.triggered.connect(self.open_file)

        self.time = np.zeros(1)
        self.counts1 = np.zeros(1)
        self.error1 = np.zeros(1)
        self.counts2 = np.zeros(1)
        self.error2 = np.zeros(1)

        self._mw.sequence_order.editingFinished.connect(self.redraw_normalized_plot)
        self._mw.contrast.editingFinished.connect(self.redraw_normalized_plot)

        self._mw.n_FFT.setMaximum(3.0e+06)
        self._mw.n_FFT.setValue(2.0e+06)

        self._mw.calculate_filter_function.clicked.connect(self._filter_function_button_fired)
        self._mw.calculate_ns.clicked.connect(self._calculate_noise_spectrum_button_fired)

        self.fit_x=np.array([0, 1])
        self.fit_y=np.array([0, 1])

        self.fit_image = pg.PlotDataItem(self.fit_x,
                                         self.fit_y,
                                         pen=pg.mkPen(palette.c3))

        # fit settings
        self._fsd = FitSettingsDialog(self.fc)
        self._fsd.sigFitsUpdated.connect(self._mw.fit_methods_ComboBox.setFitFunctions)
        self._fsd.applySettings()
        self._mw.actionFit_Settings.triggered.connect(self._fsd.show)

        self._mw.do_x_fit_PushButton.clicked.connect(self.do_x_fit)

        if 'fits' in self._statusVariables and isinstance(self._statusVariables['fits'], dict):
            self.fc.load_from_dict(self._statusVariables['fits'])
        return

    def initMainUI(self):
        """ Definition, configuration and initialisation of the confocal GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        Moreover it sets default values.
        """
        self._mw = NVdepthMainWindow()

    def initAppUI(self):
        self.ex.setWindowTitle(self.ex.title)
        self.ex.setGeometry(self.ex.left, self.ex.top, self.ex.width, self.ex.height)
        # self.openFileNamesDialog()
        # self.saveFileDialog()
        #

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self.ex, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*.dat);;Python Files (*.txt)", options=options)

        if fileName:
            print(fileName)
        return str(fileName)

    def on_deactivate(self):
        """ Reverse steps of activation

        @return int: error code (0:OK, -1:error)
        """
        self._mw.close()
        return 0

    def show(self):
        """Make main window visible and put it above all other windows. """
        # Show the Main Magnet Control GUI:
        self._mw.show()
        self._mw.activateWindow()
        self._mw.raise_()

    def open_file(self):
        self.myfile = self.openFileNameDialog()
        self.ex.show()
        self.ex.exec_()

        self.show_data()

    def show_data(self):

        f = open(self.myfile, 'r')
        lines = f.readlines()
        result = []
        for x in lines:
            result.append(x.split('#')[0])
        f.close()

        a = [x for x in result if x != '']
        self.time = np.zeros(len(a))
        self.counts1 = np.zeros(len(a))
        self.error1 = np.zeros(len(a))
        self.counts2 = np.zeros(len(a))
        self.error2 = np.zeros(len(a))

        self._mw.data_plot.clear()
        self._mw.processeddataplot.clear()

        for i in range(len(a)):
            self.time[i]=np.asarray(a[i].split(), dtype=np.float32)[0]
            self.counts1[i] = np.asarray(a[i].split(), dtype=np.float32)[1]
            self.error1[i] = np.asarray(a[i].split(), dtype=np.float32)[3]
            self.counts2[i] = np.asarray(a[i].split(), dtype=np.float32)[2]
            self.error2[i] = np.asarray(a[i].split(), dtype=np.float32)[4]

        self.data_image1 = pg.PlotDataItem(self.time,
                                     self.counts1,
                                     pen=pg.mkPen(palette.c1, style=QtCore.Qt.DotLine),
                                     symbol='o',
                                     symbolPen=palette.c1,
                                     symbolBrush=palette.c1,
                                     symbolSize=7)

        self._mw.data_plot.addItem(self.data_image1)
        self.data_image2 = pg.PlotDataItem(self.time,
                                           self.counts2,
                                           pen=pg.mkPen(palette.c3, style=QtCore.Qt.DotLine),
                                           symbol='o',
                                           symbolPen=palette.c3,
                                           symbolBrush=palette.c3,
                                           symbolSize=7)

        self._mw.data_plot.addItem(self.data_image2)
        self._mw.data_plot.setLabel(axis='left', text='Counts', units='Counts/s')
        self._mw.data_plot.setLabel(axis='bottom', text='time', units='s')
        self._mw.data_plot.showGrid(x=True, y=True, alpha=0.8)

        self.baseline = np.sum(self.counts2+self.counts1)/len(self.counts2)/2
        C0_up = self.baseline / (1 - 0.01 * self._mw.contrast.value() / 2)
        C0_down = C0_up * (1 - 0.01 * self._mw.contrast.value())
        counts = self.counts2 - self.counts1

        self.T = self.time * 8 * self._mw.sequence_order.value()

        self.normalized_counts = (counts) / (C0_up - C0_down)

        self.normalized_image = pg.PlotDataItem(self.time, #self.T,
                                           self.normalized_counts,
                                           pen=pg.mkPen(palette.c2, style=QtCore.Qt.DotLine),
                                           symbol='o',
                                           symbolPen=palette.c2,
                                           symbolBrush=palette.c2,
                                           symbolSize=7)

        self._mw.processeddataplot.addItem(self.normalized_image)
        self._mw.processeddataplot.setLabel(axis='left', text='Counts', units='Counts/s')
        self._mw.processeddataplot.setLabel(axis='bottom', text='time', units='s')
        self._mw.processeddataplot.showGrid(x=True, y=True, alpha=0.8)

    def _calculate_noise_spectrum_button_fired(self):

        self._mw.spin_noise_plot.clear()

        S = -np.log(self.normalized_counts) / self.T
        # self.S = np.concatenate((self.S, S), axis=0)

        frequency = 1e+6 * 1e-9 * 0.5e+3 / self.time  # (in Hz)

        # self.frequency = np.concatenate((self.frequency, frequency), axis=0)

        self.noise_spectrum_image = pg.PlotDataItem(frequency * 1e-6,
                                                S,
                                                pen=pg.mkPen(palette.c5, style=QtCore.Qt.DotLine),
                                                symbol='o',
                                                symbolPen=palette.c5,
                                                symbolBrush=palette.c5,
                                                symbolSize=7)

        self._mw.spin_noise_plot.addItem(self.noise_spectrum_image)
        self._mw.spin_noise_plot.setLabel(axis='left', text='Intensity', units='arb.u.')
        self._mw.spin_noise_plot.setLabel(axis='bottom', text='Frequency', units='MHz')
        self._mw.spin_noise_plot.showGrid(x=True, y=True, alpha=0.8)

    def redraw_normalized_plot(self):
        self._mw.processeddataplot.clear()

        self.baseline = np.sum(self.counts2 + self.counts1) / len(self.counts2) / 2
        C0_up = self.baseline / (1 - 0.01 * self._mw.contrast.value() / 2)
        C0_down = C0_up * (1 - 0.01 * self._mw.contrast.value())
        counts = self.counts2 - self.counts1

        self.T = self.time * 8 * self._mw.sequence_order.value()

        self.normalized_counts = (counts) / (C0_up - C0_down)

        self.normalized_image = pg.PlotDataItem(self.time, #self.T * 1.0e-6,
                                                self.normalized_counts,
                                                pen=pg.mkPen(palette.c2, style=QtCore.Qt.DotLine),
                                                symbol='o',
                                                symbolPen=palette.c2,
                                                symbolBrush=palette.c2,
                                                symbolSize=7)

        self._mw.processeddataplot.addItem(self.normalized_image)
        self._mw.processeddataplot.setLabel(axis='left', text='Counts', units='Counts/s')
        self._mw.processeddataplot.setLabel(axis='bottom', text='time', units='us')
        self._mw.processeddataplot.showGrid(x=True, y=True, alpha=0.8)
        return

    def _filter_function(self, tau):
        # generate filter function
        dt = 1e-9
        n = int(tau / dt)

        v = np.zeros(8 * self._mw.sequence_order.value() * n)

        T = np.linspace(0, dt * n * 8 * self._mw.sequence_order.value(), num=8 * self._mw.sequence_order.value() * n)
        v[:n // 2] = 1
        k = n / 2 + 1
        for j in range(8 * self._mw.sequence_order.value() - 1):
            v[(n // 2 + j * n):(n // 2 + j * n + n)] = (-1) ** (j + 1)
            k = k + 1
        v[8 * self._mw.sequence_order.value() * n - n // 2:8 * self._mw.sequence_order.value() * n] = np.ones((n // 2,), dtype=np.int)
        return T, v

    def _fourier_transform(self, tau):
        T, v = self._filter_function(tau)

        g = int(self._mw.n_FFT.value())

        signalFFT = np.fft.fft(v, g)

        yf = (np.abs(signalFFT) ** 2) * (1e-9) / (8 * self._mw.sequence_order.value())
        xf = np.fft.fftfreq(g, 1e-9)

        self.FFy = yf[0:g]  # take only real part
        self.FFx = xf[0:g]

        f1 = (1 / (2 * self.time[0])) * 1.1  # bigger
        f2 = (1 / (2 * self.time[-1])) * 0.5  # smaller

        yf1 = self.FFy[np.where(self.FFx <= f1)]
        xf1 = self.FFx[np.where(self.FFx <= f1)]

        self.FFy = self.FFy[np.where(xf1 >= f2)]
        self.FFx = self.FFx[np.where(xf1 >= f2)]
        return

    def _filter_function_button_fired(self):
        self._fourier_transform(self.time[self._mw.N_tau.value()])

        self._mw.filter_function.clear()

        self.filter_function_image = pg.PlotDataItem(self.FFx * 1e-6,
                                                     self.FFy,
                                                pen=pg.mkPen(palette.c4, style=QtCore.Qt.DotLine),
                                                symbol='o',
                                                symbolPen=palette.c4,
                                                symbolBrush=palette.c4,
                                                symbolSize=7)

        self._mw.filter_function.addItem(self.filter_function_image)
        self._mw.filter_function.setLabel(axis='left', text='Intensity', units='arb.u.')
        self._mw.filter_function.setLabel(axis='bottom', text='Frequency', units='MHz')
        self._mw.filter_function.showGrid(x=True, y=True, alpha=0.8)
        return

    @fc.constructor
    def sv_set_fits(self, val):
        # Setup fit container
        fc = self.fitlogic().make_fit_container('processed', '1d')
        fc.set_units(['s', 'c/s'])
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
            default_fits['1d'] = d1['Lorentzian peak']

            fc.load_from_dict(default_fits)
        return fc

    @fc.representer
    def sv_get_fits(self, val):
        """ save configured fits """
        if len(val.fit_list) > 0:
            return val.save_to_dict()
        else:
            return None

    def get_fit_x_functions(self):
        """ Return the hardware constraints/limits
        @return list(str): list of fit function names
        """
        return list(self.fc.fit_list)

    def do_x_fit(self, fit_function=None, x_data=None, y_data=None):
        """
        Execute the currently configured fit on the measurement data. Optionally on passed data
        """
        fit_function = self.get_fit_x_functions()[0]
        if (x_data is None) or (y_data is None):
            x_data = self.time
            y_data = self.normalized_counts

        if fit_function is not None and isinstance(fit_function, str):
            if fit_function in self.get_fit_x_functions():
                self.fc.set_current_fit(fit_function)
            else:
                self.fc.set_current_fit('No Fit')
                if fit_function != 'No Fit':
                    self.log.warning('Fit function "{0}" not available in ODMRLogic fit container.'
                                     ''.format(fit_function))
        self.fit_x, self.fit_y, result = self.fc.do_fit(x_data, y_data)
        print(result)

        if result is None:
            result_str_dict = {}
        else:
            result_str_dict = result.result_str_dict
        self.update_x_fit(self.fit_x, self.fit_y,
                                    result_str_dict, self.fc.current_fit)
        return

    def update_x_fit(self, x_data, y_data, result_str_dict, current_fit):
        """ Update the shown fit. """

        if current_fit != 'No Fit':
            # display results as formatted text
            self._mw.x_fit_result.clear()
            try:
                formated_results = units.create_formatted_output(result_str_dict)
            except:
                formated_results = 'this fit does not return formatted results'
            self._mw.x_fit_result.setPlainText(formated_results)

        self._mw.fit_methods_ComboBox.blockSignals(True)
        self._mw.fit_methods_ComboBox.setCurrentFit(current_fit)
        self._mw.fit_methods_ComboBox.blockSignals(False)

        # check which Fit method is used and remove or add again the
        # odmr_fit_image, check also whether a odmr_fit_image already exists.
        if current_fit != 'No Fit':
            self.fit_image.setData(x=x_data, y=y_data)
            if self.fit_image not in self._mw.processeddataplot.listDataItems():
                self._mw.processeddataplot.addItem(self.fit_image)
        else:
            if self.fit_image in self._mw.processeddataplot.listDataItems():
                self._mw.processeddataplot.removeItem(self.fit_image)

        # self._mw.X_scan.getViewBox().updateAutoRange()
        return
