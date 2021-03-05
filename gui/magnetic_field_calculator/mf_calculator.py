# -*- coding: utf-8 -*-

"""
This file contains the GUI for magnet control.

QuDi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

QuDi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with QuDi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import datetime
import numpy as np
import os
import pyqtgraph as pg
import pyqtgraph.exporters
from qtpy import uic

from core.module import Connector, StatusVar
from core.util.units import get_unit_prefix_dict
from gui.colordefs import ColorScaleInferno
from gui.colordefs import QudiPalettePale as palette
from gui.guibase import GUIBase
from gui.guiutils import ColorBar
from qtpy import QtCore
from qtpy import QtWidgets
from qtwidgets.scientific_spinbox import ScienDSpinBox


class CrossROI(pg.ROI):

    """ Create a Region of interest, which is a zoomable rectangular.

    @param float pos: optional parameter to set the position
    @param float size: optional parameter to set the size of the roi

    Have a look at:
    http://www.pyqtgraph.org/documentation/graphicsItems/roi.html
    """
    sigUserRegionUpdate = QtCore.Signal(object)
    sigMachineRegionUpdate = QtCore.Signal(object)

    def __init__(self, pos, size, **args):
        """Create a ROI with a central handle."""
        self.userDrag = False
        pg.ROI.__init__(self, pos, size, **args)
        # That is a relative position of the small box inside the region of
        # interest, where 0 is the lowest value and 1 is the highest:
        center = [0.5, 0.5]
        # Translate the center to the intersection point of the crosshair.
        self.addTranslateHandle(center)

        self.sigRegionChangeStarted.connect(self.startUserDrag)
        self.sigRegionChangeFinished.connect(self.stopUserDrag)
        self.sigRegionChanged.connect(self.regionUpdateInfo)

    def setPos(self, pos, update=True, finish=False):
        """Sets the position of the ROI.

        @param bool update: whether to update the display for this call of setPos
        @param bool finish: whether to emit sigRegionChangeFinished

        Changed finish from parent class implementation to not disrupt user dragging detection.
        """
        super().setPos(pos, update=update, finish=finish)


    def setSize(self, size, update=True, finish=True):
        """
        Sets the size of the ROI
        @param bool update: whether to update the display for this call of setPos
        @param bool finish: whether to emit sigRegionChangeFinished
        """
        super().setSize(size, update=update, finish=finish)


    def handleMoveStarted(self):
        """ Handles should always be moved by user."""
        super().handleMoveStarted()
        self.userDrag = True


    def startUserDrag(self, roi):
        """ROI has started being dragged by user."""
        self.userDrag = True


    def stopUserDrag(self, roi):
        """ROI has stopped being dragged by user"""
        self.userDrag = False


    def regionUpdateInfo(self, roi):
        """When the region is being dragged by the user, emit the corresponding signal."""
        if self.userDrag:
            self.sigUserRegionUpdate.emit(roi)
        else:
            self.sigMachineRegionUpdate.emit(roi)

class CrossLine(pg.InfiniteLine):

    """ Construct one line for the Crosshair in the plot.

    @param float pos: optional parameter to set the position
    @param float angle: optional parameter to set the angle of the line
    @param dict pen: Configure the pen.

    For additional options consider the documentation of pyqtgraph.InfiniteLine
    """

    def __init__(self, **args):
        pg.InfiniteLine.__init__(self, **args)
#        self.setPen(QtGui.QPen(QtGui.QColor(255, 0, 255),0.5))

    def adjust(self, extroi):
        """
        Run this function to adjust the position of the Crosshair-Line

        @param object extroi: external roi object from pyqtgraph
        """
        if self.angle == 0:
            self.setValue(extroi.pos()[1] + extroi.size()[1] * 0.5)
        if self.angle == 90:
            self.setValue(extroi.pos()[0] + extroi.size()[0] * 0.5)

class MainWindowCalculator(QtWidgets.QMainWindow):
    """ Create the Main Window based on the *.ui file. """

    def __init__(self):
        # Get the path to the *.ui file
        this_dir = os.path.dirname(__file__)
        ui_file = os.path.join(this_dir, 'mf_calculator.ui')

        # Load it
        super(MainWindowCalculator, self).__init__()
        uic.loadUi(ui_file, self)
        self.show()

class CalculatorGui(GUIBase):
    """ Main GUI for the magnet. """

    _modclass = 'CalculatorGui'
    _modtype = 'gui'

    def __init__(self, config, **kwargs):
        super().__init__(config=config, **kwargs)

        # gyromagnetic ratio of several nuclei, MHz/T
        self.nuclei_dict = {'B10':28.75/(2*np.pi), 'B11':85.84/(2*np.pi), 'C13':10.705, 'Deuterium':6.536, 'Eletron':28024.95164, 'F19':40.052, 'Hydrogen':42.576, 'N15':4.316, 'P31':17.235}

    def on_activate(self):
        """ Definition and initialisation of the GUI.
        """
        self._mw = MainWindowCalculator()
        self._mw.comboBox.clear()
        self.generate_list_of_nuclei()

        self._mw.comboBox.setCurrentIndex(list(self.nuclei_dict.keys()).index('Hydrogen'))

        self._mw.magnetic_field.setValue(500.0)
        self._mw.magnetic_field.editingFinished.connect(self.calculate_NV_transitions)
        self._mw.lower_transition.editingFinished.connect(self.calculate_magnetic_field)

        self._mw.CalculateButton.clicked.connect(self.calculate)
        return 0


    def on_deactivate(self):
        """ Deactivate the module properly.
        """
        self._mw.close()

    def generate_list_of_nuclei(self):

        for n, nucleus in enumerate(self.nuclei_dict.keys()):
            self._mw.comboBox.addItem(nucleus, n)

    def calculate_NV_transitions(self):

        g = 2.802495164*1e-3 # in GHz/Gauss

        if (2.870 - g*self._mw.magnetic_field.value()) > 0:
            self._mw.lower_transition.setValue(2.870 - g*self._mw.magnetic_field.value())
        else:
            self._mw.lower_transition.setValue(g * self._mw.magnetic_field.value() - 2.870)

        self._mw.upper_transition.setValue(2.870 + g * self._mw.magnetic_field.value())
        return

    def calculate_magnetic_field(self):

        g = 2.802495164 * 1e-3  # in GHz/Gauss

        if self._mw.checkBox.isChecked():
            self._mw.magnetic_field.setValue((2.870 + self._mw.lower_transition.value()) / g)
        else:
            self._mw.magnetic_field.setValue((2.870 - self._mw.lower_transition.value()) / g)
        self._mw.upper_transition.setValue(2.870 + g * self._mw.magnetic_field.value())
        return

    def calculate(self):

        g = self.nuclei_dict[str(self._mw.comboBox.currentText())]

        self._mw.larmor_frequency.display(g * self._mw.magnetic_field.value() / 10000)  # Larmor frequency in MHz

        self._mw.larmor_period.display(1e+3 / self._mw.larmor_frequency.value())

        self._mw.dip_position.display((1 / (2 * self._mw.larmor_frequency.value())) * 1e+3)  # in ns

