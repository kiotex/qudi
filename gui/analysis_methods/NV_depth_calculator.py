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
from numpy import trapz
from scipy.fftpack import fft
from scipy.optimize import leastsq

from core.module import Connector, ConfigOption, StatusVar
from gui.guibase import GUIBase
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
        ui_file = os.path.join(this_dir, 'NV_depth_calculator.ui')

        # Load it
        super(NVdepthMainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()

class NVdepthGui(GUIBase):

    """ Class for the alignment of the magnetic field.
    """
    _modclass = 'MagnetControlGui'
    _modtype = 'gui'

    savelogic = Connector(interface='SaveLogic')

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Initializes all needed UI files and establishes the connectors.

        This method executes the all the inits for the differnt GUIs and passes
        the event argument from fysom to the methods.
        """

        # # Getting an access to all connectors:
        self._save_logic = self.get_connector('savelogic')

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

        self._mw.g.setMaximum(5e+5)
        self._mw.g.setValue(5.0e+3)

        self._mw.a.setMaximum(50.0e-12)
        self._mw.a.setValue(9.4e-14)

        self._mw.calculate_filter_function.clicked.connect(self._filter_function_button_fired)
        self._mw.calculate_ns.clicked.connect(self._calculate_noise_spectrum_button_fired)
        self._mw.calculate_depth.clicked.connect(self._distance_to_NV_button_fired)

        # self._mw.do_x_fit_PushButton.clicked.connect(self.do_x_fit)

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

        self.time = self.time[np.where(self.time <= 268*1e-9)]
        self.counts1 = self.counts1[np.where(self.time <= 268*1e-9)]
        self.counts2 = self.counts2[np.where(self.time <= 268*1e-9)]

        self.data_image1 = pg.PlotDataItem(self.time*1e+9,
                                     self.counts1,
                                     pen=pg.mkPen(palette.c1, style=QtCore.Qt.DotLine),
                                     symbol='o',
                                     symbolPen=palette.c1,
                                     symbolBrush=palette.c1,
                                     symbolSize=7)

        self._mw.data_plot.addItem(self.data_image1)
        self.data_image2 = pg.PlotDataItem(self.time * 1e+9,
                                           self.counts2,
                                           pen=pg.mkPen(palette.c3, style=QtCore.Qt.DotLine),
                                           symbol='o',
                                           symbolPen=palette.c3,
                                           symbolBrush=palette.c3,
                                           symbolSize=7)

        self._mw.data_plot.addItem(self.data_image2)
        self._mw.data_plot.setLabel(axis='left', text='Counts', units='Counts/s')
        self._mw.data_plot.setLabel(axis='bottom', text='time', units='ns')
        self._mw.data_plot.showGrid(x=True, y=True, alpha=0.8)

        self.baseline = np.sum(self.counts2+self.counts1)/len(self.counts2)/2
        C0_up = self.baseline / (1 - 0.01 * self._mw.contrast.value() / 2)
        C0_down = C0_up * (1 - 0.01 * self._mw.contrast.value())
        counts = self.counts2 - self.counts1

        self.T = self.time * 16 * self._mw.sequence_order.value()

        self.normalized_counts = (counts) / (C0_up - C0_down)

        self.normalized_image = pg.PlotDataItem(self.time,
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

        self._filter_function_button_fired()

    def _calculate_noise_spectrum_button_fired(self):

        # 0 approximation

        x0 = 1 / (2 * self.time[np.argmin(self.normalized_counts)])

        g0 = self._mw.g.value()
        a0 = self._mw.a.value()

        self._fourier_transform(self.time[0])

        freq = self.FFx
        d = self.FFx[1] - self.FFx[0]

        delta = 0.05
        FFx = np.zeros((len(self.time), len(freq)))
        FFy = np.zeros((len(self.time), len(freq)))

        for i in range(len(self.time)):
            self._fourier_transform(self.time[i])  # now we have self.FFx and self.FFy
            FFx[i][:] = self.FFx
            FFy[i][:] = self.FFy ** 2

        dif2 = 1
        dif1 = 1
        dif = 1
        dif0 = 1

        self.k = 0.0
        self.b = 0.0

        self.x0 = x0
        self.g = g0
        self.a = a0

        # b=x0/5.0
        k = 0.0
        b = 0.0

        # find background======================================================================================================================================================================================================

        sequence = np.where(self.normalized_counts >= max(self.normalized_counts) * 0.9)[0]
        uy = np.take(self.normalized_counts, sequence)

        while True:  # optimize background

            self.b = b
            dif = dif1
            dif2 = 1
            k = 0
            while True:
                k = (k - 0.1) * 1e-8
                SS = (k * freq + b) * 1e-18
                dif1 = dif2
                hi = []
                for i in sequence:
                    Int = trapz(SS * FFy[i][:], dx=d) * 1e+18  # integration
                    hi.append(Int)
                hi = [-x for x in hi]
                cc = np.exp(hi)
                dif2 = np.sqrt(sum((cc - uy) ** 2) / (len(uy) - 1))
                if dif2 >= dif1:
                    break
            b = b + 0.001
            self.k = k

            if dif1 >= dif:
                break

        dif2 = 1
        dif1 = 1
        dif = 1

        ux = np.linspace(x0 * 0.98, x0 * 1.02, 40)

        x0 = 1 / (2 * self.time[np.argmin(self.normalized_counts)])
        g = g0
        a = a0
        while True: # optimize the dip

            self.g = g
            a = a0
            dif = dif1
            while True:  # optimize amplitude
                a = a * 1.1
                S = (a / np.pi) * g / ((freq - x0) ** 2 + g ** 2) + (self.k * freq + self.b) * 1e-18
                dif1 = dif2
                hi = []
                for i in range(len(self.time)):
                    Int = trapz(S * FFy[i][:], dx=d) * 1e+18  # integration
                    hi.append(Int)

                hi = [-x for x in hi]
                calculated_counts = np.exp(hi)

                dif2 = np.sqrt(
                    sum((calculated_counts - self.normalized_counts) ** 2) / (len(calculated_counts) - 1))
                if dif2 >= dif1:
                    break
            self.a = a
            dif2 = dif1
            g = g - 200

            if dif1 >= dif:
                break

        param = np.zeros((40))

        for i in range(len(ux)):  # optimize position
            S = (self.a / np.pi) * self.g / ((freq - ux[i]) ** 2 + self.g ** 2) + (self.k * freq + self.b) * 1e-18
            hi = []
            for j in range(len(self.time)):
                Int = trapz(S * FFy[j][:], dx=d) * 1e+18  # integration
                hi.append(Int)

            hi = [-x for x in hi]

            calculated_counts = np.exp(hi)
            param[i] = np.std(calculated_counts - self.normalized_counts)
        self.x0 = ux[np.argmin(param)]

        dif2 = 1
        dif1 = 1
        dif = 1
        g = g0
        while True:
            self.g = g
            a = a0
            dif = dif1
            while True:  # optimize amplitude
                a = a * 1.1
                S = (a / np.pi) * g / ((freq - self.x0) ** 2 + g ** 2) + (self.k * freq + self.b) * 1e-18
                dif1 = dif2
                hi = []
                for i in range(len(self.time)):
                    Int = trapz(S * FFy[i][:], dx=d) * 1e+18  # integration
                    hi.append(Int)
                hi = [-x for x in hi]
                calculated_counts = np.exp(hi)
                dif2 = np.sqrt(
                    sum((calculated_counts - self.normalized_counts) ** 2) / (len(calculated_counts) - 1))

                if dif2 >= dif1:
                    break

            self.a = a
            dif2 = dif1
            g = g - 200

            if dif1 >= dif:
                break

        self._show_calculation_button_fired()

    def _show_calculation_button_fired(self):

        d = self.FFx[1] - self.FFx[0]

        FFx = np.zeros((len(self.time), len(self.FFx)))
        FFy = np.zeros((len(self.time), len(self.FFx)))

        for i in range(len(self.time)):
            self._fourier_transform(self.time[i])  # now we have self.FFx and self.FFy
            FFx[i][:] = self.FFx
            FFy[i][:] = self.FFy ** 2

        self._mw.a.setValue(self.a)
        self._mw.g.setValue(self.g)

        self.S = (self.a / np.pi) * self.g / ((self.FFx - self.x0) ** 2 + self.g ** 2) + (
                                                                                         self.k * self.FFx + self.b) * 1e-18

        self._mw.spin_noise_plot.clear()
        self.noise_spectrum_image = pg.PlotDataItem(self.FFx,
                                                    self.S * 1e18,
                                                    pen=pg.mkPen(palette.c5, style=QtCore.Qt.DotLine),
                                                    symbol='o',
                                                    symbolPen=palette.c5,
                                                    symbolBrush=palette.c5,
                                                    symbolSize=7)

        self._mw.spin_noise_plot.addItem(self.noise_spectrum_image)
        self._mw.spin_noise_plot.setLabel(axis='left', text='Intensity', units='arb.u.')
        self._mw.spin_noise_plot.setLabel(axis='bottom', text='Frequency', units='Hz')
        self._mw.spin_noise_plot.showGrid(x=True, y=True, alpha=0.8)

        hi = []
        hi1 = []

        for i in range(len(self.time)):
            Int = trapz(self.S * FFy[i][:], dx=d) * 1e+18  # integration
            hi.append(Int)
            Int1 = trapz((self.k * self.FFx + self.b) * FFy[i][:], dx=d)  # integration
            hi1.append(Int1)

        hi = [-x for x in hi]
        hi1 = [-x for x in hi1]
        calculated_counts = np.exp(hi)

        self._mw.error_approximation.display(100 * np.sum(
            np.abs(calculated_counts - self.normalized_counts) / calculated_counts) / len(self.normalized_counts))

        try:
            self._mw.processeddataplot.removeItem(self.fit_image)
            self._mw.processeddataplot.removeItem(self.baseline_image)
        except: print(1)

        self.fit_image = pg.PlotDataItem(self.time,
                                         calculated_counts,
                                                pen=pg.mkPen(palette.c6, style=QtCore.Qt.DotLine),
                                                symbol='o',
                                                symbolPen=palette.c6,
                                                symbolBrush=palette.c6,
                                                symbolSize=7
                                         )
        self._mw.processeddataplot.addItem(self.fit_image)

        self.baseline_image = pg.PlotDataItem(self.time,
                                         np.exp(hi1),
                                         pen=pg.mkPen(palette.c6, style=QtCore.Qt.DotLine),
                                         symbol='o',
                                         symbolPen=palette.c6,
                                         symbolBrush=palette.c6,
                                         symbolSize=7
                                         )
        self._mw.processeddataplot.addItem(self.baseline_image)

    def redraw_normalized_plot(self):
        self._mw.processeddataplot.clear()

        self.baseline = np.sum(self.counts2 + self.counts1) / len(self.counts2) / 2
        C0_up = self.baseline / (1 - 0.01 * self._mw.contrast.value() / 2)
        C0_down = C0_up * (1 - 0.01 * self._mw.contrast.value())
        counts = self.counts2 - self.counts1

        self.T = self.time * 16 * self._mw.sequence_order.value()

        self.normalized_counts = (counts) / (C0_up - C0_down)

        self.normalized_image = pg.PlotDataItem(self.T * 1.0e-6,
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

        v = np.zeros(16 * self._mw.sequence_order.value() * n)

        T = np.linspace(0, dt * n * 16 * self._mw.sequence_order.value(), num=16 * self._mw.sequence_order.value() * n)
        v[:n // 2] = 1
        k = n / 2 + 1
        for j in range(16 * self._mw.sequence_order.value() - 1):
            v[(n // 2 + j * n):(n // 2 + j * n + n)] = (-1) ** (j + 1)
            k = k + 1
        v[16 * self._mw.sequence_order.value() * n - n // 2:16 * self._mw.sequence_order.value() * n] = np.ones((n // 2,), dtype=np.int)
        return T, v

    def _fourier_transform(self, tau):
        T, v = self._filter_function(tau)

        g = int(self._mw.n_FFT.value())

        signalFFT = np.fft.fft(v, g)

        yf = (np.abs(signalFFT) ** 2) * (1e-9) / (16 * self._mw.sequence_order.value())
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
                                                symbolSize=4)

        self._mw.filter_function.addItem(self.filter_function_image)
        self._mw.filter_function.setLabel(axis='left', text='Intensity', units='arb.u.')
        self._mw.filter_function.setLabel(axis='bottom', text='Frequency', units='MHz')
        self._mw.filter_function.showGrid(x=True, y=True, alpha=0.8)
        return

    def _distance_to_NV_button_fired(self):

        rho_H = 5 * 1e+28  # m^(-3), density of protons
        # rho_B11 = 2.1898552552552544e+28  # m^(-3), density of B11

        mu_p = 1.41060674333 * 1e-26  # proton magneton, J/T
        g_B11 = 85.847004 * 1e+6 / (2 * np.pi)  # Hz/T
        hbar = 1.054571800e-34  # J*s
        # mu_B11 = hbar * g_B11 * 2 * np.pi  # for central transition

        rho = rho_H
        mu = mu_p

        g = 2 * np.pi * 2.8 * 1e+10  # rad/s/T
        mu0 = 4 * np.pi * 1e-7  # vacuum permeability, H/m or T*m/A

        freq = self.FFx  # in Hz
        d = self.FFx[1] - self.FFx[0]

        S = self.S * 1e+18

        base = (self.k * self.FFx + self.b)

        Int = trapz((S - base), dx=d)  # integration

        self._mw.Brms.display(np.sqrt(2 * Int))

        self._mw.z.display(np.power(rho * ((0.05 * mu0 * mu / self._mw.Brms.value() * 1e9) ** 2), 1 / 3.)*1e+9)
        # elif self.substance == 'hBN, B11 signal':
        #     C1 = np.sqrt(0.654786) / (4 * np.pi)
        #     self.z = np.power(rho * ((C1 * mu0 * mu / self.Brms * 1e9) ** 2), 1 / 3.)

        self._mw.error_depth.display(self._mw.error_approximation.value() * self._mw.z.value()/ 100)
        self._mw.Brms_error.display(self._mw.error_approximation.value() * self._mw.Brms.value() / 100)

        self.base_image = pg.PlotDataItem(self.FFx,
                                          base,
                                                    pen=pg.mkPen(palette.c6, style=QtCore.Qt.DotLine),
                                                    symbol='o',
                                                    symbolPen=palette.c6,
                                                    symbolBrush=palette.c6,
                                                    symbolSize=5)

        self._mw.spin_noise_plot.addItem(self.base_image)

