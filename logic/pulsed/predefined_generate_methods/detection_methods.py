# -*- coding: utf-8 -*-

"""
This file contains the Qudi Nuclear spin detection Methods for sequence generator

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
from logic.pulsed.pulse_objects import PulseBlock, PulseBlockEnsemble, PulseSequence
from logic.pulsed.pulse_objects import PredefinedGeneratorBase


"""
General Pulse Creation Procedure:
=================================
- Create at first each PulseBlockElement object
- add all PulseBlockElement object to a list and combine them to a
  PulseBlock object.
- Create all needed PulseBlock object with that idea, that means
  PulseBlockElement objects which are grouped to PulseBlock objects.
- Create from the PulseBlock objects a PulseBlockEnsemble object.
- If needed and if possible, combine the created PulseBlockEnsemble objects
  to the highest instance together in a PulseSequence object.
"""


class DetectionGenerator(PredefinedGeneratorBase):
    """

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_XY16_seq(self, name='XY16_seq', tau_start=250e-9, tau_step=1.0e-9, num_of_points=5,
                             xy16_order=2, alternating=True):
        """
        Generate XY16 decoupling sequence
        """
        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # get tau array for measurement ticks
        tau_array = tau_start + np.arange(num_of_points) * tau_step

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()
        print(self.rabi_period)

        pihalf_element = self._get_mw_rf_element(length = self.rabi_period / 4,
                                                 increment = 0,
                                                 amp1=self.microwave_amplitude,
                                                 freq1=self.microwave_frequency,
                                                 phase1=0,
                                                 amp2=0.0,
                                                 freq2=self.microwave_frequency,
                                                 phase2=0)

        last_pihalf_element = self._get_mw_rf_gate_element(length = self.rabi_period / 4,
                                                 increment = 0,
                                                 amp1=self.microwave_amplitude,
                                                 freq1=self.microwave_frequency,
                                                 phase1=0,
                                                 amp2=0.0,
                                                 freq2=self.microwave_frequency,
                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length = self.rabi_period / 2,
                                                 increment = 0,
                                                 amp1=self.microwave_amplitude,
                                                 freq1=self.microwave_frequency,
                                                 phase1=0,
                                                 amp2=0.0,
                                                 freq2=self.microwave_frequency,
                                                 phase2=0)

        pi_y_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=90.0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        pi_minus_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=180.0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        pi_minus_y_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                                     increment=0,
                                                     amp1=self.microwave_amplitude,
                                                     freq1=self.microwave_frequency,
                                                     phase1=270.0,
                                                     amp2=0.0,
                                                     freq2=self.microwave_frequency,
                                                     phase2=0)

        pi3half_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                     increment=0,
                                                     amp1=self.microwave_amplitude,
                                                     freq1=self.microwave_frequency,
                                                     phase1=180.0,
                                                     amp2=0.0,
                                                     freq2=self.microwave_frequency,
                                                     phase2=0)

        sequence_list = []
        i=0

        for t in tau_array:

            tauhalf_element = self._get_idle_element(length=t/2 - self.rabi_period/4, increment=0)
            tau_element = self._get_idle_element(length = t - self.rabi_period/2, increment=0.0)
            wfm_list = []
            wfm_list.extend([pihalf_element, tauhalf_element])

            for j in range(xy16_order-1):
                wfm_list.extend([pi_x_element, tau_element, pi_y_element, tau_element, pi_x_element, tau_element,
                                 pi_y_element, tau_element, pi_y_element, tau_element, pi_x_element, tau_element,
                                 pi_y_element, tau_element, pi_x_element, tau_element, pi_minus_x_element, tau_element,
                                 pi_minus_y_element, tau_element, pi_minus_x_element,tau_element, pi_minus_y_element, tau_element,
                                 pi_minus_y_element, tau_element, pi_minus_x_element, tau_element, pi_minus_y_element, tau_element,
                                 pi_minus_x_element, tau_element])

            wfm_list.extend([pi_x_element, tau_element, pi_y_element, tau_element, pi_x_element, tau_element,
                                 pi_y_element, tau_element, pi_y_element, tau_element, pi_x_element, tau_element,
                                 pi_y_element, tau_element, pi_x_element, tau_element, pi_minus_x_element, tau_element,
                                 pi_minus_y_element, tau_element, pi_minus_x_element,tau_element, pi_minus_y_element, tau_element,
                                 pi_minus_y_element, tau_element, pi_minus_x_element, tau_element, pi_minus_y_element, tau_element,
                                 pi_minus_x_element, tauhalf_element, last_pihalf_element])

            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'XY16u_%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, tau_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                wfm_list2.extend([pihalf_element, tauhalf_element])

                for j in range(xy16_order - 1):
                    wfm_list2.extend([pi_x_element, tau_element, pi_y_element, tau_element, pi_x_element, tau_element,
                                     pi_y_element, tau_element, pi_y_element, tau_element, pi_x_element, tau_element,
                                     pi_y_element, tau_element, pi_x_element, tau_element, pi_minus_x_element, tau_element,
                                     pi_minus_y_element, tau_element, pi_minus_x_element, tau_element, pi_minus_y_element,
                                     tau_element,
                                     pi_minus_y_element, tau_element, pi_minus_x_element, tau_element, pi_minus_y_element,
                                     tau_element,
                                     pi_minus_x_element, tau_element])

                wfm_list2.extend([pi_x_element, tau_element, pi_y_element, tau_element, pi_x_element, tau_element,
                                 pi_y_element, tau_element, pi_y_element, tau_element, pi_x_element, tau_element,
                                 pi_y_element, tau_element, pi_x_element, tau_element, pi_minus_x_element, tau_element,
                                 pi_minus_y_element, tau_element, pi_minus_x_element, tau_element, pi_minus_y_element,
                                 tau_element,
                                 pi_minus_y_element, tau_element, pi_minus_x_element, tau_element, pi_minus_y_element,
                                 tau_element,
                                 pi_minus_x_element, tauhalf_element, pi3half_element])

                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'XY16d_%02i' % i
                blocks, decoupling2 = self._generate_waveform(wfm_list2, name2, tau_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(decoupling2)
                sequence_list.append((decoupling2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

        #---------------------------------------------------------------------------------------------------------------
        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = tau_array
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = num_of_points
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences