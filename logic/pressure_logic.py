# -*- coding: utf-8 -*-
"""
Laser management.

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

import time
import numpy as np
from qtpy import QtCore

from core.connector import Connector
from core.configoption import ConfigOption
from logic.generic_logic import GenericLogic


class PressureLogic(GenericLogic):
    """ Logic module agreggating multiple hardware switches.
    """

    # waiting time between queries im milliseconds
    APC = Connector(interface='ProcessControlInterface')
    gauge1 = Connector(interface='ProcessInterface', optional=True)
    gauge2 = Connector(interface='ProcessInterface', optional=True)

    queryInterval = ConfigOption('query_interval', 100)

    sigUpdate = QtCore.Signal()
    sigUpdateObjectiveSV = QtCore.Signal()

    def on_activate(self):
        """ Prepare logic module for work.
        """
        self._APC = self.APC()
        self.stopRequest = False
        self.bufferLength = 100
        self.data = {}

        self._APC_minimal_step = self.get_minimal_step()
        self.SV = self._APC.get_control_value()
        self.set_control_value(self.SV)
        self._last_updated_time = time.time()

        self._gauge1 = self.gauge1()
        self._gauge2 = self.gauge2()

        self.decleasing_speed = 1
        self.incleasing_speed = 1

        # delay timer for querying pressure
        self.queryTimer = QtCore.QTimer()
        self.queryTimer.setInterval(self.queryInterval)
        self.queryTimer.setSingleShot(True)
        self.queryTimer.timeout.connect(
            self.check_pressure_loop,
            QtCore.Qt.QueuedConnection)

        self.init_data_logging()
        self.start_query_loop()

    def on_deactivate(self):
        """ Deactivate modeule.
        """
        self.stop_query_loop()
        for i in range(5):
            time.sleep(self.queryInterval / 1000)
            QtCore.QCoreApplication.processEvents()

    @QtCore.Slot()
    def check_pressure_loop(self):
        """ Get power, current, shutter state and temperatures from laser. """
        if self.stopRequest:
            if self.module_state.can('stop'):
                self.module_state.stop()
            self.stopRequest = False
            return
        qi = self.queryInterval
        try:
            now = time.time()

            #print('pressureloop', QtCore.QThread.currentThreadId())
            self.PV = self._APC.get_process_value()
            self.SV = self._APC.get_control_value()

            if self._last_SV != self.SV:  # APC本体側でSVを操作したときの値を反映させる。
                self._objective_SV = self.SV
                self.sigUpdateObjectiveSV.emit()

            if self.SV > self._objective_SV:  # 減少させたいとき
                if now - self._last_updated_time >= self.decleasing_speed:
                    self.SV -= self._APC_minimal_step
                    self._APC.set_control_value(self.SV)
                    self._last_updated_time = now

            elif self.SV < self._objective_SV:  # 増加させたいとき
                if now - self._last_updated_time >= self.incleasing_speed:
                    self.SV += self._APC_minimal_step
                    self._APC.set_control_value(self.SV)
                    self._last_updated_time = now

            self._last_SV = self.SV

            for k in self.data:
                self.data[k] = np.roll(self.data[k], -1)

            self.data['PV'][-1] = self.PV
            self.data['SV'][-1] = self.SV
            self.data['time'][-1] = now

            if self._gauge1 is not None:
                self.data[self._gauge1.get_name(
                )][-1] = self._gauge1.get_process_value()
            if self._gauge2 is not None:
                self.data[self._gauge2.get_name(
                )][-1] = self._gauge2.get_process_value()

        except BaseException:
            qi = 3000
            self.log.exception(
                "Exception in laser status loop, throttling refresh rate.")

        self.queryTimer.start(qi)
        self.sigUpdate.emit()

    @QtCore.Slot()
    def start_query_loop(self):
        """ Start the readout loop. """
        self.module_state.run()
        self.queryTimer.start(self.queryInterval)

    @QtCore.Slot()
    def stop_query_loop(self):
        """ Stop the readout loop. """
        self.stopRequest = True
        for i in range(10):
            if not self.stopRequest:
                return
            QtCore.QCoreApplication.processEvents()
            time.sleep(self.queryInterval / 1000)

    def init_data_logging(self):
        """ Zero all log buffers. """
        #self.data['PV'] = np.zeros(self.bufferLength)
        #self.data['SV'] = np.zeros(self.bufferLength)
        self.data['PV'] = np.ones(
            self.bufferLength) * self._APC.get_process_value()
        self.data['SV'] = np.ones(
            self.bufferLength) * self._APC.get_control_value()
        self._last_SV = self._APC.get_control_value()
        self.data['time'] = np.ones(self.bufferLength) * time.time()

        if self._gauge1 is not None:
            #self.data[ self._gauge1.get_name() ] = np.zeros(self.bufferLength)
            self.data[self._gauge1.get_name()] = np.ones(
                self.bufferLength) * self._gauge1.get_process_value()
        if self._gauge2 is not None:
            self.data[self._gauge2.get_name()] = np.ones(
                self.bufferLength) * self._gauge2.get_process_value()

    @QtCore.Slot()
    def get_process_unit(self):
        return self._APC.get_process_unit()

    @QtCore.Slot()
    def get_control_limit(self):
        return self._APC.get_control_limit()

    @QtCore.Slot(float)
    def get_control_value(self):
        return self.SV

    @QtCore.Slot(float)
    def get_objective_control_value(self):
        return self._objective_SV

    @QtCore.Slot(float)
    def get_process_value(self):
        if self._gauge1 is not None:
            if self.data['CAP'][-1] >= 0.5e3:
                return self.data['CAP'][-1]
            else:
                return self.data['C-ION'][-1]
        else:
            return self.PV

    @QtCore.Slot(float)
    def get_minimal_step(self):
        return self._APC.get_minimal_step()

    @QtCore.Slot(float)
    def set_control_value(self, setValue):
        """ Set laser diode current. """
        self._objective_SV = setValue
        self._last_updated_time = time.time()
