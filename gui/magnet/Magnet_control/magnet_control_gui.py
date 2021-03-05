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
from core.util import units

class MagnetControlMainWindow(QtWidgets.QMainWindow):

    """ Create the Mainwindow based on the corresponding *.ui file. """

    sigPressKeyBoard = QtCore.Signal(QtCore.QEvent)

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'magnet_control.ui')

        # Load it
        super(MagnetControlMainWindow, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()

    # def keyPressEvent(self, event):
    #     """Pass the keyboard press event from the main window further. """
    #     self.sigPressKeyBoard.emit(event)

class MagnetControlSettingDialog(QtWidgets.QDialog):
    """ The settings dialog for ODMR measurements.
    """
    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'magnet_control.ui')

        # Load it
        super(MagnetControlSettingDialog, self).__init__()
        uic.loadUi(ui_file, self)


class MagnetControlGui(GUIBase):

    """ Class for the alignment of the magnetic field.
    """
    _modclass = 'MagnetControlGui'
    _modtype = 'gui'

    # declare connectors
    magnetlogic1 = Connector(interface='MagnetController')
    savelogic = Connector(interface='SaveLogic')

    # signals
    sigFitXChanged = QtCore.Signal(str)
    sigDoXFit = QtCore.Signal(str)
    sigFitYChanged = QtCore.Signal(str)
    sigDoYFit = QtCore.Signal(str)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Initializes all needed UI files and establishes the connectors.

        This method executes the all the inits for the differnt GUIs and passes
        the event argument from fysom to the methods.
        """

        # # Getting an access to all connectors:
        self._magnet_logic = self.get_connector('magnetlogic1')
        self._save_logic = self.get_connector('savelogic')
        self._hardware_state = True

        self.initMainUI()      # initialize the main GUI

        # Get the image from the logic
        self.imageX = pg.PlotDataItem(self._magnet_logic.fluor_plot_x,
                                      self._magnet_logic.fluor_plot_y,
                                     pen=pg.mkPen(palette.c1, style=QtCore.Qt.DotLine),
                                     symbol='o',
                                     symbolPen=palette.c1,
                                     symbolBrush=palette.c1,
                                     symbolSize=7)

        self.imageY = pg.PlotDataItem(self._magnet_logic.yfluor_plot_x,
                                      self._magnet_logic.yfluor_plot_y,
                                      pen=pg.mkPen(palette.c1, style=QtCore.Qt.DotLine),
                                      symbol='o',
                                      symbolPen=palette.c1,
                                      symbolBrush=palette.c1,
                                      symbolSize=7)

        self.fluor_x_fit_image = pg.PlotDataItem(self._magnet_logic.x_scan_fit_x,
                                              self._magnet_logic.x_scan_fit_y,
                                              pen=pg.mkPen(palette.c2))
        self.fluor_y_fit_image = pg.PlotDataItem(self._magnet_logic.y_scan_fit_x,
                                                 self._magnet_logic.y_scan_fit_y,
                                                 pen=pg.mkPen(palette.c2))

        # Add the display item to the X_scan and Y_scan, which were defined in the UI file.
        self._mw.X_scan.addItem(self.imageX)
        self._mw.X_scan.setLabel(axis='left', text='Counts', units='Counts/s')
        self._mw.X_scan.setLabel(axis='bottom', text='X axis', units='mm')
        self._mw.X_scan.showGrid(x=True, y=True, alpha=0.8)

        self._mw.Y_scan.addItem(self.imageY)
        self._mw.Y_scan.setLabel(axis='left', text='Counts', units='Counts/s')
        self._mw.Y_scan.setLabel(axis='bottom', text='X axis', units='mm')
        self._mw.Y_scan.showGrid(x=True, y=True, alpha=0.8)

        ########################################################################
        #          Configuration of the various display Widgets                #
        ########################################################################
        # Take the default values from logic:
        self._mw.x_start.setValue(self._magnet_logic.x_start)
        self._mw.x_end.setValue(self._magnet_logic.x_end)
        self._mw.step_x.setValue(self._magnet_logic.step_x)

        self._mw.y_start.setValue(self._magnet_logic.y_start)
        self._mw.y_end.setValue(self._magnet_logic.y_end)
        self._mw.step_y.setValue(self._magnet_logic.step_y)

        self._mw.acq_time.setValue(self._magnet_logic.fluorescence_integration_time)
        self._mw.N_AF_points.setValue(self._magnet_logic.N_AF_points)

        self._mw.set_x_pos.setValue(self._magnet_logic.set_x_pos)
        self._mw.set_y_pos.setValue(self._magnet_logic.set_y_pos)
        self._mw.set_z_pos.setValue(self._magnet_logic.set_z_pos)

        # fit settings
        self._fsd = FitSettingsDialog(self._magnet_logic.fc)
        self._fsd.sigFitsUpdated.connect(self._mw.fit_methods_ComboBox.setFitFunctions)
        self._fsd.sigFitsUpdated.connect(self._mw.fit_methods_ComboBox_2.setFitFunctions)
        self._fsd.applySettings()
        self._mw.action_FitSettings.triggered.connect(self._fsd.show)

        ########################################################################
        #                       Connect signals                                #
        ########################################################################
        # Internal user input changed signals
        self._mw.x_start.editingFinished.connect(self.change_x_start)
        self._mw.x_end.editingFinished.connect(self.change_x_end)
        self._mw.step_x.editingFinished.connect(self.change_step_x)

        self._mw.y_start.editingFinished.connect(self.change_y_start)
        self._mw.y_end.editingFinished.connect(self.change_y_end)
        self._mw.step_y.editingFinished.connect(self.change_step_y)

        self._mw.acq_time.editingFinished.connect(self.change_acq_time)
        self._mw.N_AF_points.editingFinished.connect(self.change_N_AF_points)

        self._mw.set_x_pos.editingFinished.connect(self.change_set_x_pos)
        self._mw.set_y_pos.editingFinished.connect(self.change_set_y_pos)
        self._mw.set_z_pos.editingFinished.connect(self.change_set_z_pos)

        self._mw.do_x_fit_PushButton.clicked.connect(self.do_x_fit)
        self.sigDoXFit.connect(self._magnet_logic.do_x_fit, QtCore.Qt.QueuedConnection)
        self._magnet_logic.sigFitXUpdated.connect(self.update_x_fit, QtCore.Qt.QueuedConnection)

        self._mw.do_y_fit_PushButton.clicked.connect(self.do_y_fit)
        self.sigDoYFit.connect(self._magnet_logic.do_y_fit, QtCore.Qt.QueuedConnection)
        self._magnet_logic.sigFitYUpdated.connect(self.update_y_fit, QtCore.Qt.QueuedConnection)

        #################################################################
        #                           Actions                             #
        #################################################################
        # Connect the scan actions to the events if they are clicked. Connect
        # also the adjustment of the displayed windows.
        self._mw.action_stop_scanning.triggered.connect(self.ready_clicked)

        self._scan_x_start_proxy = pg.SignalProxy(
            self._mw.action_scan_x_start.triggered,
            delay=0.1,
            slot=self.x_scan_clicked
        )

        self._scan_y_start_proxy = pg.SignalProxy(
            self._mw.action_scan_y_start.triggered,
            delay=0.1,
            slot=self.y_scan_clicked
        )

        self._magnet_logic.sigPlotXUpdated.connect(self.update_x_plot, QtCore.Qt.QueuedConnection)
        self._magnet_logic.sigPlotYUpdated.connect(self.update_y_plot, QtCore.Qt.QueuedConnection)
        self._magnet_logic.sigPositionUpdated.connect(self.get_current_position)

        self._magnet_logic.signal_stop_scanning.connect(self.ready_clicked)

        self._mw.currposbutton.clicked.connect(self.get_current_position)
        self._mw.appl_pos_butt.clicked.connect(self.apply_position)
        self._mw.Set_pos_button.clicked.connect(self.set_position)

        self.get_current_position()

        return

    def initMainUI(self):
        """ Definition, configuration and initialisation of the confocal GUI.

        This init connects all the graphic modules, which were created in the
        *.ui file and configures the event handling between the modules.
        Moreover it sets default values.
        """
        self._mw = MagnetControlMainWindow()

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

        ############################################################################
        #                           Change Methods                                 #
        ############################################################################

    def change_x_start(self):
        """ Update the starting position along x axis in the logic according to the GUI.
        """
        self._magnet_logic.x_start = self._mw.x_start.value()
        return

    def change_x_end(self):
        """ Update the final position along x axis in the logic according to the GUI.
        """
        self._magnet_logic.x_end = self._mw.x_end.value()
        return

    def change_step_x(self):
        """ Update step along x axis in the logic according to the GUI.
        """
        self._magnet_logic.step_x = self._mw.step_x.value()
        if self._magnet_logic.x_start!=0 and self._magnet_logic.x_end!=0:
            self._mw.n_x_points.setValue(len(np.arange(self._mw.x_start.value(), self._mw.x_end.value(), self._mw.step_x.value())))
            self._magnet_logic.n_x_points = self._mw.n_x_points.value()
        return

    def change_y_start(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        self._magnet_logic.y_start = self._mw.y_start.value()
        return

    def change_y_end(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        self._magnet_logic.y_end = self._mw.y_end.value()
        return

    def change_step_y(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        self._magnet_logic.step_y = self._mw.step_y.value()
        if self._magnet_logic.y_start!=0 and self._magnet_logic.y_end!=0:
            self._mw.n_y_points.setValue(len(np.arange(self._mw.y_start.value(), self._mw.y_end.value(), self._mw.step_y.value())))
            self._magnet_logic.n_y_points = self._mw.n_y_points.value()
        return

    def change_acq_time(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        self._magnet_logic.fluorescence_integration_time = self._mw.acq_time.value()
        return

    def change_N_AF_points(self):
        """ Update the xy resolution in the logic according to the GUI.
        """
        self._magnet_logic.N_AF_points = self._mw.N_AF_points.value()
        return

    def change_set_x_pos(self):
        """ Update the starting position along x axis in the logic according to the GUI.
        """
        self._magnet_logic.set_x_pos = self._mw.set_x_pos.value()

        return

    def change_set_y_pos(self):
        """ Update the final position along x axis in the logic according to the GUI.
        """
        self._magnet_logic.set_y_pos = self._mw.set_y_pos.value()
        return

    def change_set_z_pos(self):
        """ Update step along x axis in the logic according to the GUI.
        """
        self._magnet_logic.set_z_pos = self._mw.set_z_pos.value()
        return

    def get_current_position(self):
        """ Update current actuators position in the logic according to the GUI.
                """
        self._magnet_logic.get_current_position()
        time.sleep(0.1)
        self._mw.curr_x_pos.setValue(self._magnet_logic.curr_x_pos)
        self._mw.curr_y_pos.setValue(self._magnet_logic.curr_y_pos)
        self._mw.curr_z_pos.setValue(self._magnet_logic.curr_z_pos)

        return

    def apply_position(self):
        """ Update current actuators position in the logic according to the GUI.
                """

        self._mw.set_x_pos.setValue(self._mw.curr_x_pos.value())
        self._mw.set_y_pos.setValue(self._mw.curr_y_pos.value())
        self._mw.set_z_pos.setValue(self._mw.curr_z_pos.value())

        self._magnet_logic.set_x_pos = self._mw.set_x_pos.value()
        self._magnet_logic.set_y_pos = self._mw.set_y_pos.value()
        self._magnet_logic.set_z_pos = self._mw.set_z_pos.value()
        return

    def set_position(self):

        self._magnet_logic.set_position()
        return

    def x_scan_clicked(self):
        """ Manages what happens if the xy scan is started. """
        self.disable_scan_actions()
        self._magnet_logic.start_x_scanning(tag='gui')


    def y_scan_clicked(self):
        """ Manages what happens if the xy scan is started. """
        self.disable_scan_actions()
        self._magnet_logic.start_y_scanning(tag='gui')

    def disable_scan_actions(self):
        """ Disables the buttons for scanning.
        """
        # Ensable the stop scanning button
        self._mw.action_stop_scanning.setEnabled(True)

        # Disable the start scan buttons
        self._mw.action_scan_x_start.setEnabled(False)
        self._mw.action_scan_y_start.setEnabled(False)

        self._mw.set_x_pos.setEnabled(False)
        self._mw.set_y_pos.setEnabled(False)
        self._mw.set_z_pos.setEnabled(False)

        self._mw.acq_time.setEnabled(False)

        self._mw.x_start.setEnabled(False)
        self._mw.x_end.setEnabled(False)
        self._mw.step_x.setEnabled(False)

        self._mw.y_start.setEnabled(False)
        self._mw.y_end.setEnabled(False)
        self._mw.step_y.setEnabled(False)

        self._mw.N_AF_points.setEnabled(False)

    def enable_scan_actions(self):
        """ Disables the buttons for scanning.
        """
        # Disable the start scan buttons
        self._mw.action_scan_x_start.setEnabled(True)
        self._mw.action_scan_y_start.setEnabled(True)

        self._mw.set_x_pos.setEnabled(True)
        self._mw.set_y_pos.setEnabled(True)
        self._mw.set_z_pos.setEnabled(True)

        self._mw.acq_time.setEnabled(True)

        self._mw.x_start.setEnabled(True)
        self._mw.x_end.setEnabled(True)
        self._mw.step_x.setEnabled(True)

        self._mw.y_start.setEnabled(True)
        self._mw.y_end.setEnabled(True)
        self._mw.step_y.setEnabled(True)

        self._mw.N_AF_points.setEnabled(True)

    def ready_clicked(self):
        """ Stopp the scan if the state has switched to ready. """
        if self._magnet_logic.module_state() == 'idle':
            self._magnet_logic.stopRequested=True
            self.enable_scan_actions()

    def update_x_plot(self, data_x, data_y):
        """ Refresh the plot widgets with new data. """
        # Update mean signal plot
        self.imageX.setData(data_x, data_y)

    def update_y_plot(self, data_x, data_y):
        """ Refresh the plot widgets with new data. """
        # Update mean signal plot
        self.imageY.setData(data_x, data_y)

    def do_x_fit(self):
        fit_function  = self._mw.fit_methods_ComboBox.getCurrentFit()[0]
        self.sigDoXFit.emit(fit_function)
        return

    def do_y_fit(self):
        fit_function  = self._mw.fit_methods_ComboBox.getCurrentFit()[0]
        self.sigDoYFit.emit(fit_function)
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
            self.fluor_x_fit_image.setData(x=x_data, y=y_data)
            if self.fluor_x_fit_image not in self._mw.X_scan.listDataItems():
                self._mw.X_scan.addItem(self.fluor_x_fit_image)
        else:
            if self.fluor_x_fit_image in self._mw.X_scan.listDataItems():
                self._mw.X_scan.removeItem(self.fluor_x_fit_image)

        self._mw.X_scan.getViewBox().updateAutoRange()
        return

    def update_y_fit(self, x_data, y_data, result_str_dict, current_fit):
        """ Update the shown fit. """
        if current_fit != 'No Fit':
            # display results as formatted text
            self._mw.y_fit_result.clear()
            try:
                formated_results = units.create_formatted_output(result_str_dict)
            except:
                formated_results = 'this fit does not return formatted results'
            self._mw.y_fit_result.setPlainText(formated_results)

        self._mw.fit_methods_ComboBox.blockSignals(True)
        self._mw.fit_methods_ComboBox.setCurrentFit(current_fit)
        self._mw.fit_methods_ComboBox.blockSignals(False)

        # check which Fit method is used and remove or add again the
        # odmr_fit_image, check also whether a odmr_fit_image already exists.
        if current_fit != 'No Fit':
            self.fluor_y_fit_image.setData(x=x_data, y=y_data)
            if self.fluor_y_fit_image not in self._mw.Y_scan.listDataItems():
                self._mw.Y_scan.addItem(self.fluor_y_fit_image)
        else:
            if self.fluor_y_fit_image in self._mw.Y_scan.listDataItems():
                self._mw.Y_scan.removeItem(self.fluor_y_fit_image)

        self._mw.Y_scan.getViewBox().updateAutoRange()
        return

    def save_data(self):
        """ Save the sum plot, the scan marix plot and the scan data """
        filetag = self._mw.save_tag_LineEdit.text()
        cb_range = self.get_matrix_cb_range()

        # Percentile range is None, unless the percentile scaling is selected in GUI.
        pcile_range = None
        if self._mw.odmr_cb_centiles_RadioButton.isChecked():
            low_centile = self._mw.odmr_cb_low_percentile_DoubleSpinBox.value()
            high_centile = self._mw.odmr_cb_high_percentile_DoubleSpinBox.value()
            pcile_range = [low_centile, high_centile]

        self.sigSaveMeasurement.emit(filetag, cb_range, pcile_range)
        return

