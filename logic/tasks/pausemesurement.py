# -*- coding: utf-8 -*-
"""
Pause measurement preposttask.

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

from logic.generic_task import PrePostTask
import time

class Task(PrePostTask):
    """ A task to pause measurement before and after another task
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print('Task {0} added!'.format(self.name))
        #print('config: ', self.config)

        self.pausing_measurement = getattr(self.ref['measurement_logic'], self.config['pausing_method'])
        self.resumeing_measurement = getattr(self.ref['measurement_logic'], self.config['resumeing_method'])

        self._measurement_was_paused = False

    def preExecute(self):
        """ Pausing measurement if it's running.
        """
        if self.ref['measurement_logic'].module_state.isstate('locked'):
            self.pausing_measurement()
            self._measurement_was_paused = True

        while self._measurement_was_paused and self.ref['measurement_logic'].module_state() != 'idle':
            time.sleep(0.1)
            print("pre", self.name)

    def postExecute(self):
        """ Resuming measurement if it was paused.
        """
        if self._measurement_was_paused:
            self._measurement_was_paused = False
            self.resumeing_measurement()
            print("post", self.name)
