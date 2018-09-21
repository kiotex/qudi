# -*- coding: utf-8 -*-

"""
This file contains the Qudi Nuclear spin polarisation Methods for sequence generator

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
class PolarizationGenerator(PredefinedGeneratorBase):
    """

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_Hartmann_Hahn_tau_sequence(self, name='HHtauseq', spinlock_amp=0.2, tau_start=30*1e-6, tau_step=2*1e-6,
                                            num_of_points=5, alternating = True):

        """
        This pulse sequence correspond to standard Hartmann-Hahn spin-locking protocol, T1pho measurement
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

        pihalf_x_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                 increment=0,
                                                 amp1=self.microwave_amplitude,
                                                 freq1=self.microwave_frequency,
                                                 phase1=0,
                                                 amp2=0.0,
                                                 freq2=self.microwave_frequency,
                                                 phase2=0)

        last_pihalf_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                           increment=0,
                                                           amp1=self.microwave_amplitude,
                                                           freq1=self.microwave_frequency,
                                                           phase1=0,
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
        i = 0

        for t in tau_array:

            # get spinlock element
            sl_element = self._get_mw_rf_element(length= t,
                                                       increment=0,
                                                       amp1=spinlock_amp,
                                                       freq1=self.microwave_frequency,
                                                       phase1=90.0,
                                                       amp2=0.0,
                                                       freq2=self.microwave_frequency,
                                                       phase2=0)

            # make sequence waveform
            name1 = 'LOCK_%02i' % i
            blocks, lock = self._generate_waveform([pihalf_x_element, sl_element, last_pihalf_element, laser_element,
                                                    delay_element, waiting_element], name1, tau_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(lock)

            sequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                name2 = 'LOCK2_%02i' % i
                blocks, lock2 = self._generate_waveform([pihalf_x_element, sl_element, pi3half_element, laser_element,
                                                        delay_element, waiting_element], name2, tau_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(lock2)

                sequence_list.append((lock2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

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

    def generate_HHampsweep(self, name='HHampsweep', spinlock_length=20e-6, spinlock_amp_start=0.12,
                                   spinlock_amp_end=0.095, num_of_points=50, alternating = True):

        """
        This pulse sequence correspond to Hartmann-Hahn spin-locking with amplitude sweep, locking time is fixed
        """

        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # get tau array for measurement ticks
        amp_array = np.linspace(spinlock_amp_start, spinlock_amp_end, num_of_points)

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()

        pihalf_x_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                 increment=0,
                                                 amp1=self.microwave_amplitude,
                                                 freq1=self.microwave_frequency,
                                                 phase1=0,
                                                 amp2=0.0,
                                                 freq2=self.microwave_frequency,
                                                 phase2=0)

        last_pihalf_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                           increment=0,
                                                           amp1=self.microwave_amplitude,
                                                           freq1=self.microwave_frequency,
                                                           phase1=0,
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
        i = 0

        for spinlock_amp in amp_array:
            sl_element = self._get_mw_rf_element(length= spinlock_length,
                                                      increment=0,
                                                      amp1=spinlock_amp,
                                                      freq1=self.microwave_frequency,
                                                      phase1=90.0,
                                                      amp2=0.0,
                                                      freq2=self.microwave_frequency,
                                                      phase2=0)

            # make sequence waveform
            name1 = 'LOCK_%02i' % i
            blocks, lock = self._generate_waveform([pihalf_x_element, sl_element, last_pihalf_element, laser_element,
                                                    delay_element, waiting_element], name1, amp_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(lock)

            sequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                name2 = 'LOCK2_%02i' % i
                blocks, lock2 = self._generate_waveform([pihalf_x_element, sl_element, pi3half_element, laser_element,
                                                        delay_element, waiting_element], name2, amp_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(lock2)

                sequence_list.append((lock2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = amp_array
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = num_of_points
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences


    def generate_Hartmann_Hahn_waiting(self, name='HHwait', spinlock_amp=0.2, lock_time = 100.0*1e-6,
                                       idle_time = 2.0*1e-6, alternating = True):

        """
        This pulse sequence correspond to standard Hartmann-Hahn spin-locking protocol, T1pho measurement
        """

        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()

        idle_element = self._get_idle_element(length=idle_time, increment=0)
        init_element = self._get_laser_init_element(length=self.laser_length, increment=0)

        pihalf_x_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                 increment=0,
                                                 amp1=self.microwave_amplitude,
                                                 freq1=self.microwave_frequency,
                                                 phase1=0,
                                                 amp2=0.0,
                                                 freq2=self.microwave_frequency,
                                                 phase2=0)

        last_pihalf_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                           increment=0,
                                                           amp1=self.microwave_amplitude,
                                                           freq1=self.microwave_frequency,
                                                           phase1=0,
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
        i = 0

        # get spinlock element
        sl_element = self._get_mw_rf_element(length= lock_time,
                                                   increment=0,
                                                   amp1=spinlock_amp,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90.0,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        # make sequence waveform

        blocks, lock = self._generate_waveform([init_element, delay_element, waiting_element, pihalf_x_element,
                                                sl_element, last_pihalf_element, laser_element,
                                                delay_element, waiting_element, idle_element],
                                                'Lock', [idle_time], 1)
        created_blocks.extend(blocks)
        created_ensembles.append(lock)

        sequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        blocks, lock2 = self._generate_waveform([init_element, delay_element, waiting_element,
                                                 pihalf_x_element, sl_element, pi3half_element, laser_element,
                                                delay_element, waiting_element, idle_element],
                                                'Lock2', [idle_time], 1)
        created_blocks.extend(blocks)
        created_ensembles.append(lock2)

        sequence_list.append((lock2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = [idle_time]
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = 1
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences

