# -*- coding: utf-8 -*-

"""
This file contains a gui for the laser controller logic.

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

from core.connector import Connector
from core.util import units

from gui.colordefs import QudiPalettePale as palette
from gui.guibase import GUIBase

from qtpy import QtCore
from qtpy import QtWidgets
from qtpy import uic


class TimeAxisItem(pg.AxisItem):
    """ pyqtgraph AxisItem that shows a HH:MM:SS timestamp on ticks.
        X-Axis must be formatted as (floating point) Unix time.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enableAutoSIPrefix(False)

    def tickStrings(self, values, scale, spacing):
        """ Hours:Minutes:Seconds string from float unix timestamp. """
        return [time.strftime("%H:%M:%S", time.localtime(value)) for value in values]


class PressureWindow(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'ui_pressure.ui')

        # Load it
        super().__init__()
        uic.loadUi(ui_file, self)
        self.show()


class PressureGUI(GUIBase):
    """ FIXME: Please document
    """

    ## declare connectors
    pressurelogic = Connector(interface='PressureLogic')

    sigSetValue = QtCore.Signal(float)

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

    def on_activate(self):
        """ Definition and initialisation of the GUI plus staring the measurement.
        """
        self._pressure_logic = self.pressurelogic()
        
        self.unit, self.unit_name = self._pressure_logic.get_process_unit()

        #####################
        # Configuring the dock widgets
        # Use the inherited class 'CounterMainWindow' to create the GUI window
        self._mw = PressureWindow()

        # Setup dock widgets
        self._mw.setDockNestingEnabled(True)
        self._mw.actionReset_View.triggered.connect(self.restoreDefaultView)
        
        
        
        self._limit_min, self._limit_max = self._pressure_logic.get_control_limit()
        self._mw.setValueDoubleSpinBox.setMaximum( self._limit_max )
        self._mw.setValueDoubleSpinBox.setMinimum( self._limit_min )
        
        self._mw.setValueDoubleSpinBox.setMinimalStep( self._pressure_logic.get_minimal_step() )
        self._mw.setValueDoubleSpinBox.setValue( self._pressure_logic.get_control_value() )
        
        self._mw.setValueDoubleSpinBox.setSingleStep(.1)#上下ボタンとかで有効数字何桁動かすか
        
        
        
        
        
        # set up plot
        self._mw.plotWidget = pg.PlotWidget(
            axisItems={'bottom': TimeAxisItem(orientation='bottom')})
        self._mw.pwContainer.layout().addWidget(self._mw.plotWidget)

        plot1 = self._mw.plotWidget.getPlotItem()
        plot1.setLabel('left', self.unit_name, units=self.unit)
        plot1.setLabel('bottom', 'Time', units=None)
        plot1.setLimits(yMin=0)
        
        #plot1.setLogMode(False, True)
        plot1.addLegend()

        self.curves = {}
        colorlist = (palette.c1, palette.c2, palette.c3, palette.c4, palette.c5, palette.c6)
        i = 0
        for name in self._pressure_logic.data:
            if name != 'time':
                curve = pg.PlotDataItem(name=name)
                curve.setPen(colorlist[i % len(colorlist)])
                plot1.addItem(curve)
                
                self.curves[name] = curve
                i += 1
        
        
        self.plot1 = plot1
        
        
        self._mw.setValueDoubleSpinBox.editingFinished.connect( self.checkSV )
        self._mw.applySetValueButton.clicked.connect( self.changeSetValue )
        self.sigSetValue.connect(self._pressure_logic.set_control_value)
        
        self._pressure_logic.sigUpdate.connect(self.updateGui)
        self._pressure_logic.sigUpdateObjectiveSV.connect(self.updateObjectiveSV)

    def on_deactivate(self):
        """ Deactivate the module properly.
        """
        self._mw.close()

    def show(self):
        """Make window visible and put it above all other windows.
        """
        QtWidgets.QMainWindow.show(self._mw)
        self._mw.activateWindow()
        self._mw.raise_()

    def restoreDefaultView(self):
        """ Restore the arrangement of DockWidgets to the default
        """
        # Show any hidden dock widgets
        self._mw.plotDockWidget.show()

        # re-dock any floating dock widgets
        self._mw.plotDockWidget.setFloating(False)

        # Arrange docks widgets
        self._mw.addDockWidget(QtCore.Qt.DockWidgetArea(1), self._mw.plotDockWidget)


    @QtCore.Slot()
    def changeSetValue(self):
        self.sigSetValue.emit( self._mw.setValueDoubleSpinBox.value() )

    @QtCore.Slot()
    def updateObjectiveSV(self):
        self._mw.setValueDoubleSpinBox.setValue( self._pressure_logic.get_objective_control_value() )

    @QtCore.Slot()
    def checkSV(self):
        SV = self._mw.setValueDoubleSpinBox.value()
        if SV == self._limit_max:
            self.log.warning("最大圧力{0:6.1r}{1}に設定されてますが大丈夫ですか？".format(units.ScaledFloat( self._limit_max ), self.unit))
        if SV < 100 and SV > 0:
            self._mw.setValueDoubleSpinBox.setValue( SV*1e3 )
            self.log.warning("{0} Paから{0} kPaに修正しました。".format(SV))



    @QtCore.Slot()
    def updateGui(self):
        """ Update labels, the plot and button states with new data. """
        self._mw.processValueLabel.setText(
            '{0:6.1r}{1}'.format(
                units.ScaledFloat(self._pressure_logic.get_process_value()),
                self.unit))
                
        for name, curve in self.curves.items():
            curve.setData(x=self._pressure_logic.data['time'], y=self._pressure_logic.data[name])
