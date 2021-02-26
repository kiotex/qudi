# -*- coding: utf-8 -*-
"""
Confocal-refocus task.

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

from logic.generic_task import InterruptableTask
import time
from qtpy import QtCore

class Task(InterruptableTask):
    """ This task does a confocal focus optimization.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print('Task {0} added!'.format(self.name))

        self.initial_pos_updated = False

        # Connect callback for a finished refocus
        self.ref['optimizer'].sigRefocusFinished.connect(
            self._optimization_callback, QtCore.Qt.QueuedConnection)

    def __del__(self):
        # Disconnect signals
        self.ref['optimizer'].sigRefocusFinished.disconnect()
        super().__del__()

    def startTask(self):
        """ Get position from scanning device and do the refocus """
        if not self.initial_pos_updated:
            self.initial_pos = self.ref['optimizer']._scanning_device.get_scanner_position()
            self.caller_tag = 'task'
        self.ref['optimizer'].start_refocus(self.initial_pos, self.caller_tag)

    def runTaskStep(self):
        """ Wait for refocus to finish. """
        time.sleep(0.1)
        return self.ref['optimizer'].module_state.isstate('locked')

    def pauseTask(self):
        """ pausing a refocus is forbidden """
        pass

    def resumeTask(self):
        """ pausing a refocus is forbidden """
        pass

    def cleanupTask(self):
        """ nothing to clean up, optimizer can do that by itself """
        self.initial_pos_updated = False

    def checkExtraStartPrerequisites(self):
        """ Check whether anything we need is locked. """
        self.log.info(f'Refocus {self.name}')
        return (
            not self.ref['optimizer']._scanning_device.module_state.isstate('locked')
            and not self.ref['optimizer'].module_state.isstate('locked')
            )

    def checkExtraPausePrerequisites(self):
        """ pausing a refocus is forbidden """
        return False


    def _optimization_callback(self, caller_tag, optimal_pos):
        """
        Callback function for a finished position optimisation.

        @param caller_tag:
        @param optimal_pos:
        """
        self.caller_tag = caller_tag
        self.optimal_pos = optimal_pos

    @property
    def refocus_XY_size(self):
        return self.ref['optimizer'].refocus_XY_size
