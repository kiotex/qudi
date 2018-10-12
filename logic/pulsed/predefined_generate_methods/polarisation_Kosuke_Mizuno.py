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


class PolarizationTransferGenerator(PredefinedGeneratorBase):
    """

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_cpmg_tau_seq(self, name='cpmg_tau_seq', tau_start=250e-9, tau_step=1.0e-9, num_of_points=5, pulse_num=8, alternating=True):
        """
        Generate CPMG dynamical (de)coupling sequence
        sweeping interpulse spacing, tau
        Y(pi/2) -- tau/2 -- X(pi) -- tau -- X(pi) -- ... -- X(pi) -- tau/2 -- Y(+/- pi/2)
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

        pihalf_y_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)
        last_pihalf_y_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                             increment=0,
                                                             amp1=self.microwave_amplitude,
                                                             freq1=self.microwave_frequency,
                                                             phase1=90,
                                                             amp2=0.0,
                                                             freq2=self.microwave_frequency,
                                                             phase2=0)

        last_pihalf_y_inv_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                                 increment=0,
                                                                 amp1=self.microwave_amplitude,
                                                                 freq1=self.microwave_frequency,
                                                                 phase1=270,
                                                                 amp2=0.0,
                                                                 freq2=self.microwave_frequency,
                                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        sequence_list = []
        i = 0

        for t in tau_array:

            tauhalf_element = self._get_idle_element(length=t / 2 - self.rabi_period / 4, increment=0)
            tau_element = self._get_idle_element(length=t - self.rabi_period / 2, increment=0.0)
            wfm_list = []

            wfm_list.extend([pihalf_y_element, tauhalf_element])
            for j in range(pulse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, last_pihalf_y_element])
            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'CPMGu_%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, tau_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                wfm_list2.extend([pihalf_y_element, tauhalf_element])
                for j in range(pulse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, last_pihalf_y_inv_element])
                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'CPMGd_%02i' % i
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

    def generate_cpmg_tau_withDC_seq(self, name='cpmg_tau_seq', tau_start=250e-9, tau_step=1.0e-9, num_of_points=5, pulse_num=8, voltage=0, alternating=True):
        """
        Generate CPMG dynamical (de)coupling sequence
        sweeping interpulse spacing, tau
        Y(pi/2) -- tau/2 -- X(pi) -- tau -- X(pi) -- ... -- X(pi) -- tau/2 -- Y(+/- pi/2)
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

        pihalf_y_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        last_pihalf_y_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                             increment=0,
                                                             amp1=self.microwave_amplitude,
                                                             freq1=self.microwave_frequency,
                                                             phase1=90,
                                                             amp2=0.0,
                                                             freq2=self.microwave_frequency,
                                                             phase2=0)

        last_pihalf_y_inv_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                                 increment=0,
                                                                 amp1=self.microwave_amplitude,
                                                                 freq1=self.microwave_frequency,
                                                                 phase1=270,
                                                                 amp2=0.0,
                                                                 freq2=self.microwave_frequency,
                                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        sequence_list = []
        i = 0

        for t in tau_array:

            tauhalf_element_plus = self._get_dc_element(length=t / 2 - self.rabi_period / 4, increment=0, vol1=voltage, vol2=0)
            tauhalf_element_minus = self._get_dc_element(length=t / 2 - self.rabi_period / 4, increment=0, vol1=-voltage, vol2=0)
            tau_element_plus = self._get_dc_element(length=t - self.rabi_period / 2, increment=0.0, vol1=voltage, vol2=0)
            tau_element_minus = self._get_dc_element(length=t - self.rabi_period / 2, increment=0.0, vol1=-voltage, vol2=0)

            tau_elements = {1: tau_element_plus, -1: tau_element_minus}
            tauhalf_elements = {1: tauhalf_element_plus, -1: tauhalf_element_minus}

            wfm_list = []

            wfm_list.extend([pihalf_y_element, tauhalf_elements[1]])
            sign = -1
            for j in range(pulse_num - 1):
                wfm_list.extend([pi_x_element, tau_elements[sign]])
                sign *= -1
            wfm_list.extend([pi_x_element, tauhalf_elements[sign], last_pihalf_y_element])
            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'CPMGu_%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, tau_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                wfm_list2.extend([pihalf_y_element, tauhalf_elements[1]])
                sign = -1
                for j in range(pulse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_elements[sign]])
                    sign *= -1
                wfm_list2.extend([pi_x_element, tauhalf_elements[sign], last_pihalf_y_inv_element])
                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'CPMGd_%02i' % i
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

    def generate_cpmg_N_seq(self, name='cpmg_N_seq', N_start=1, N_step=1, num_of_points=16, tau=0.1e-6, alternating=True):
        """
        Generate CPMG dynamical (de)coupling sequence
        sweeping num of pulse
        Y(pi/2) -- tau/2 -- X(pi) -- tau -- X(pi) -- ... -- X(pi) -- tau/2 -- Y(+/- pi/2)
        """
        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # get tau array for measurement ticks
        N_array = (N_start + np.arange(num_of_points) * N_step).astype(np.int)

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()
        print(self.rabi_period)

        pihalf_y_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        last_pihalf_y_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                             increment=0,
                                                             amp1=self.microwave_amplitude,
                                                             freq1=self.microwave_frequency,
                                                             phase1=90,
                                                             amp2=0.0,
                                                             freq2=self.microwave_frequency,
                                                             phase2=0)

        last_pihalf_y_inv_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                                 increment=0,
                                                                 amp1=self.microwave_amplitude,
                                                                 freq1=self.microwave_frequency,
                                                                 phase1=270,
                                                                 amp2=0.0,
                                                                 freq2=self.microwave_frequency,
                                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        sequence_list = []
        i = 0

        for Np in N_array:

            tauhalf_element = self._get_idle_element(length=tau / 2 - self.rabi_period / 4, increment=0)
            tau_element = self._get_idle_element(length=tau - self.rabi_period / 2, increment=0.0)
            wfm_list = []

            wfm_list.extend([pihalf_y_element, tauhalf_element])
            for j in range(Np - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, last_pihalf_y_element])
            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'CPMG_N_u_N%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, N_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                wfm_list2.extend([pihalf_y_element, tauhalf_element])
                for j in range(Np - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, last_pihalf_y_inv_element])
                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'CPMG_N_d_N%02i' % i
                blocks, decoupling2 = self._generate_waveform(wfm_list2, name2, N_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(decoupling2)
                sequence_list.append((decoupling2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

        #---------------------------------------------------------------------------------------------------------------
        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = N_array
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = num_of_points
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences

    def generate_cpmg_corr(self, name='cpmg_corr_seq', tcorr_start=10e-6, tcorr_step=1e-6, num_of_points=16, tau=0.1e-6, pluse_num=8, alternating=True):
        """
        Generate correlation CPMG dynamical (de)coupling sequence
        sweeping correlation time
        Y(pi/2) - DD - X(pi/2) -- tcorr -- X(pi/2) - DD - Y(+/- pi/2)
        """
        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # get tau array for measurement ticks
        tcorr_array = tcorr_start + np.arange(num_of_points) * tcorr_step

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()
        print(self.rabi_period)

        pihalf_x_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=0,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        pihalf_y_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        last_pihalf_y_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                             increment=0,
                                                             amp1=self.microwave_amplitude,
                                                             freq1=self.microwave_frequency,
                                                             phase1=90,
                                                             amp2=0.0,
                                                             freq2=self.microwave_frequency,
                                                             phase2=0)

        last_pihalf_y_inv_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                                 increment=0,
                                                                 amp1=self.microwave_amplitude,
                                                                 freq1=self.microwave_frequency,
                                                                 phase1=270,
                                                                 amp2=0.0,
                                                                 freq2=self.microwave_frequency,
                                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        sequence_list = []
        i = 0

        for tcorr in tcorr_array:

            tauhalf_element = self._get_idle_element(length=tau / 2 - self.rabi_period / 4, increment=0)
            tau_element = self._get_idle_element(length=tau - self.rabi_period / 2, increment=0.0)
            tcorr_element = self._get_idle_element(length=tcorr - self.rabi_period / 4, increment=0.0)
            wfm_list = []

            #   Y(pi/2) - DD - X(pi/2) -- tcorr -- X(pi/2) - DD - Y(+/- pi/2)
            wfm_list.extend([pihalf_y_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, pihalf_x_element])
            wfm_list.extend([tcorr_element])
            wfm_list.extend([pihalf_x_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, last_pihalf_y_element])
            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'CPMG_corr_u_N%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, tcorr_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                wfm_list2.extend([pihalf_y_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, pihalf_x_element])
                wfm_list2.extend([tcorr_element])
                wfm_list2.extend([pihalf_x_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, last_pihalf_y_inv_element])
                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'CPMG_corr_d_N%02i' % i
                blocks, decoupling2 = self._generate_waveform(wfm_list2, name2, tcorr_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(decoupling2)
                sequence_list.append((decoupling2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

        #---------------------------------------------------------------------------------------------------------------
        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = tcorr_array
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = num_of_points
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences

    def generate_cpmg_corr_flip(self, name='cpmg_corr_flip_seq', tcorr_start=10e-6, tcorr_step=1e-6, num_of_points=16, tau=0.1e-6, pluse_num=8, alternating=True):
        """
        Generate correlation CPMG dynamical (de)coupling sequence
        sweeping correlation time
        Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X - tcorr/2 -- X(pi/2) - DD - Y(+/- pi/2)
        """
        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # get tau array for measurement ticks
        tcorr_array = tcorr_start + np.arange(num_of_points) * tcorr_step

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()
        print(self.rabi_period)

        pihalf_x_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=0,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        pihalf_y_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        last_pihalf_y_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                             increment=0,
                                                             amp1=self.microwave_amplitude,
                                                             freq1=self.microwave_frequency,
                                                             phase1=90,
                                                             amp2=0.0,
                                                             freq2=self.microwave_frequency,
                                                             phase2=0)

        last_pihalf_y_inv_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                                 increment=0,
                                                                 amp1=self.microwave_amplitude,
                                                                 freq1=self.microwave_frequency,
                                                                 phase1=270,
                                                                 amp2=0.0,
                                                                 freq2=self.microwave_frequency,
                                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        sequence_list = []
        i = 0

        for tcorr in tcorr_array:

            tauhalf_element = self._get_idle_element(length=tau / 2 - self.rabi_period / 4, increment=0)
            tau_element = self._get_idle_element(length=tau - self.rabi_period / 2, increment=0.0)
            tcorrhalf_element = self._get_idle_element(length=tcorr / 2 - self.rabi_period / 4 - self.rabi_period / 8, increment=0.0)
            wfm_list = []

            #   Y(pi/2) - DD - X(pi/2) -- tcorr -- X(pi/2) - DD - Y(+/- pi/2)
            wfm_list.extend([pihalf_y_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, pihalf_x_element])
            wfm_list.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
            wfm_list.extend([pihalf_x_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, last_pihalf_y_element])
            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'CPMG_corr_flip_u_N%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, tcorr_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                wfm_list2.extend([pihalf_y_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, pihalf_x_element])
                wfm_list.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
                wfm_list2.extend([pihalf_x_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, last_pihalf_y_inv_element])
                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'CPMG_corr_flip_d_N%02i' % i
                blocks, decoupling2 = self._generate_waveform(wfm_list2, name2, tcorr_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(decoupling2)
                sequence_list.append((decoupling2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

        #---------------------------------------------------------------------------------------------------------------
        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = tcorr_array
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = num_of_points
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences

    def generate_poltransfer(self, name='poltrans_seq', t_start=0.1e-6, t_step=1e-0, num_of_points=16, tau=0.1e-6, tcorr=0.1e-6, pluse_num=8, alternating=True):
        """
        Generate correlation CPMG dynamical (de)coupling sequence
        Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(+/- pi/2)

        This function is base of poltrans_xxx_seq, simply repeating identical sequence by num_of_points times.
        """
        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # get tau array for measurement ticks
        t_array = t_start + np.arange(num_of_points) * t_step

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()
        print(self.rabi_period)

        pihalf_x_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=0,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        pihalf_y_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        last_pihalf_y_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                             increment=0,
                                                             amp1=self.microwave_amplitude,
                                                             freq1=self.microwave_frequency,
                                                             phase1=90,
                                                             amp2=0.0,
                                                             freq2=self.microwave_frequency,
                                                             phase2=0)

        last_pihalf_y_inv_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                                 increment=0,
                                                                 amp1=self.microwave_amplitude,
                                                                 freq1=self.microwave_frequency,
                                                                 phase1=270,
                                                                 amp2=0.0,
                                                                 freq2=self.microwave_frequency,
                                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        pi_x_inv_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=180,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        sequence_list = []
        i = 0

        for t in t_array:
            tauhalf_element = self._get_idle_element(length=tau / 2 - self.rabi_period / 4, increment=0)
            tau_element = self._get_idle_element(length=tau - self.rabi_period / 2, increment=0.0)
            tcorrhalf_element = self._get_idle_element(length=tcorr / 2 - self.rabi_period / 4, increment=0.0)
            wfm_list = []

            #   Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(-/+ pi/2)
            wfm_list.extend([pihalf_y_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, pihalf_x_element])
            wfm_list.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
            wfm_list.extend([pi_x_inv_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, last_pihalf_y_inv_element])
            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'PolTransfer_u_N%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, t_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                #   Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(-/+ pi/2)
                wfm_list2.extend([pihalf_y_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, pihalf_x_element])
                wfm_list2.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
                wfm_list2.extend([pi_x_inv_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, last_pihalf_y_element])
                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'PolTransfer_d_N%02i' % i
                blocks, decoupling2 = self._generate_waveform(wfm_list2, name2, t_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(decoupling2)
                sequence_list.append((decoupling2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

        #---------------------------------------------------------------------------------------------------------------
        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = t_array
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = num_of_points
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences

    def generate_poltransfer_tcorr_seq(self, name='poltrans_tcorr_seq', t_start=0.1e-6, t_step=1e-0, num_of_points=16, tau=0.1e-6, pluse_num=8, alternating=True):
        """
        Generate correlation CPMG dynamical (de)coupling sequence
        Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(+/- pi/2)
        """
        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # get tau array for measurement ticks
        t_array = t_start + np.arange(num_of_points) * t_step

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()
        print(self.rabi_period)

        pihalf_x_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=0,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        pihalf_y_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        last_pihalf_y_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                             increment=0,
                                                             amp1=self.microwave_amplitude,
                                                             freq1=self.microwave_frequency,
                                                             phase1=90,
                                                             amp2=0.0,
                                                             freq2=self.microwave_frequency,
                                                             phase2=0)

        last_pihalf_y_inv_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                                 increment=0,
                                                                 amp1=self.microwave_amplitude,
                                                                 freq1=self.microwave_frequency,
                                                                 phase1=270,
                                                                 amp2=0.0,
                                                                 freq2=self.microwave_frequency,
                                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        pi_x_inv_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=180,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        sequence_list = []
        i = 0

        for tcorr in t_array:
            tauhalf_element = self._get_idle_element(length=tau / 2 - self.rabi_period / 4, increment=0)
            tau_element = self._get_idle_element(length=tau - self.rabi_period / 2, increment=0.0)
            tcorrhalf_element = self._get_idle_element(length=tcorr / 2 - self.rabi_period / 4, increment=0.0)
            wfm_list = []

            #   Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(-/+ pi/2)
            wfm_list.extend([pihalf_y_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, pihalf_x_element])
            wfm_list.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
            wfm_list.extend([pi_x_inv_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, last_pihalf_y_inv_element])
            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'PolTransfer_tcorr_u_N%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, t_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                #   Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(-/+ pi/2)
                wfm_list2.extend([pihalf_y_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, pihalf_x_element])
                wfm_list2.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
                wfm_list2.extend([pi_x_inv_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, last_pihalf_y_element])
                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'PolTransfer_tcorr_d_N%02i' % i
                blocks, decoupling2 = self._generate_waveform(wfm_list2, name2, t_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(decoupling2)
                sequence_list.append((decoupling2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

        #---------------------------------------------------------------------------------------------------------------
        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = t_array
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = num_of_points
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences

    def generate_poltransfer_tau_seq(self, name='poltrans_tau_seq', t_start=0.1e-6, t_step=1e-0, num_of_points=16, tcorr=0.1e-6, pluse_num=8, alternating=True):
        """
        Generate correlation CPMG dynamical (de)coupling sequence
        Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(+/- pi/2)
        """
        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # get tau array for measurement ticks
        t_array = t_start + np.arange(num_of_points) * t_step

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()
        print(self.rabi_period)

        pihalf_x_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=0,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        pihalf_y_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        last_pihalf_y_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                             increment=0,
                                                             amp1=self.microwave_amplitude,
                                                             freq1=self.microwave_frequency,
                                                             phase1=90,
                                                             amp2=0.0,
                                                             freq2=self.microwave_frequency,
                                                             phase2=0)

        last_pihalf_y_inv_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                                 increment=0,
                                                                 amp1=self.microwave_amplitude,
                                                                 freq1=self.microwave_frequency,
                                                                 phase1=270,
                                                                 amp2=0.0,
                                                                 freq2=self.microwave_frequency,
                                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        pi_x_inv_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=180,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        sequence_list = []
        i = 0

        for tau in t_array:
            tauhalf_element = self._get_idle_element(length=tau / 2 - self.rabi_period / 4, increment=0)
            tau_element = self._get_idle_element(length=tau - self.rabi_period / 2, increment=0.0)
            tcorrhalf_element = self._get_idle_element(length=tcorr / 2 - self.rabi_period / 4, increment=0.0)
            wfm_list = []

            #   Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(-/+ pi/2)
            wfm_list.extend([pihalf_y_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, pihalf_x_element])
            wfm_list.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
            wfm_list.extend([pi_x_inv_element, tauhalf_element])
            for j in range(pluse_num - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, last_pihalf_y_inv_element])
            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'PolTransfer_tau_u_N%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, t_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                #   Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(-/+ pi/2)
                wfm_list2.extend([pihalf_y_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, pihalf_x_element])
                wfm_list2.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
                wfm_list2.extend([pi_x_inv_element, tauhalf_element])
                for j in range(pluse_num - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, last_pihalf_y_element])
                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'PolTransfer_tau_d_N%02i' % i
                blocks, decoupling2 = self._generate_waveform(wfm_list2, name2, t_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(decoupling2)
                sequence_list.append((decoupling2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

        #---------------------------------------------------------------------------------------------------------------
        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = t_array
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = num_of_points
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences

    def generate_poltransfer_N_seq(self, name='poltrans_tau_seq', N_start=1, N_step=1, num_of_points=16, tau=0.1e-6, tcorr=0.1e-6, alternating=True):
        """
        Generate correlation CPMG dynamical (de)coupling sequence
        Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(+/- pi/2)
        """
        created_blocks = list()
        created_ensembles = list()
        created_sequences = list()

        # get tau array for measurement ticks
        N_array = (N_start + np.arange(num_of_points) * N_step).astype(np.int)

        # create the static waveform elements
        waiting_element = self._get_idle_element(length=self.wait_time, increment=0)
        laser_element = self._get_laser_element(length=self.laser_length, increment=0)
        delay_element = self._get_delay_element()
        print(self.rabi_period)

        pihalf_x_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=0,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        pihalf_y_element = self._get_mw_rf_element(length=self.rabi_period / 4,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=90,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        last_pihalf_y_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                             increment=0,
                                                             amp1=self.microwave_amplitude,
                                                             freq1=self.microwave_frequency,
                                                             phase1=90,
                                                             amp2=0.0,
                                                             freq2=self.microwave_frequency,
                                                             phase2=0)

        last_pihalf_y_inv_element = self._get_mw_rf_gate_element(length=self.rabi_period / 4,
                                                                 increment=0,
                                                                 amp1=self.microwave_amplitude,
                                                                 freq1=self.microwave_frequency,
                                                                 phase1=270,
                                                                 amp2=0.0,
                                                                 freq2=self.microwave_frequency,
                                                                 phase2=0)

        pi_x_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                               increment=0,
                                               amp1=self.microwave_amplitude,
                                               freq1=self.microwave_frequency,
                                               phase1=0,
                                               amp2=0.0,
                                               freq2=self.microwave_frequency,
                                               phase2=0)

        pi_x_inv_element = self._get_mw_rf_element(length=self.rabi_period / 2,
                                                   increment=0,
                                                   amp1=self.microwave_amplitude,
                                                   freq1=self.microwave_frequency,
                                                   phase1=180,
                                                   amp2=0.0,
                                                   freq2=self.microwave_frequency,
                                                   phase2=0)

        sequence_list = []
        i = 0

        for N in N_array:
            tauhalf_element = self._get_idle_element(length=tau / 2 - self.rabi_period / 4, increment=0)
            tau_element = self._get_idle_element(length=tau - self.rabi_period / 2, increment=0.0)
            tcorrhalf_element = self._get_idle_element(length=tcorr / 2 - self.rabi_period / 4, increment=0.0)
            wfm_list = []

            #   Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(-/+ pi/2)
            wfm_list.extend([pihalf_y_element, tauhalf_element])
            for j in range(N - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, pihalf_x_element])
            wfm_list.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
            wfm_list.extend([pi_x_inv_element, tauhalf_element])
            for j in range(N - 1):
                wfm_list.extend([pi_x_element, tau_element])
            wfm_list.extend([pi_x_element, tauhalf_element, last_pihalf_y_inv_element])
            wfm_list.extend([laser_element, delay_element, waiting_element])

            name1 = 'PolTransfer_tau_u_N%02i' % i
            blocks, decoupling = self._generate_waveform(wfm_list, name1, N_array, 1)
            created_blocks.extend(blocks)
            created_ensembles.append(decoupling)

            sequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                wfm_list2 = []
                #   Y(pi/2) - DD - X(pi/2) -- tcorr/2 - X(pi) - tcorr/2 -- X(-pi) - DD - Y(-/+ pi/2)
                wfm_list2.extend([pihalf_y_element, tauhalf_element])
                for j in range(N - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, pihalf_x_element])
                wfm_list2.extend([tcorrhalf_element, pi_x_element, tcorrhalf_element])
                wfm_list2.extend([pi_x_inv_element, tauhalf_element])
                for j in range(N - 1):
                    wfm_list2.extend([pi_x_element, tau_element])
                wfm_list2.extend([pi_x_element, tauhalf_element, last_pihalf_y_element])
                wfm_list2.extend([laser_element, delay_element, waiting_element])

                name2 = 'PolTransfer_tau_d_N%02i' % i
                blocks, decoupling2 = self._generate_waveform(wfm_list2, name2, N_array, 1)
                created_blocks.extend(blocks)
                created_ensembles.append(decoupling2)
                sequence_list.append((decoupling2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            i = i + 1

        #---------------------------------------------------------------------------------------------------------------
        created_sequence = PulseSequence(name=name, ensemble_list=sequence_list, rotating_frame=True)

        created_sequence.measurement_information['alternating'] = True
        created_sequence.measurement_information['laser_ignore_list'] = list()
        created_sequence.measurement_information['controlled_variable'] = N_array
        created_sequence.measurement_information['units'] = ('s', '')
        created_sequence.measurement_information['number_of_lasers'] = num_of_points
        # created_sequence.measurement_information['counting_length'] = self._get_ensemble_count_length(
        #     ensemble=block_ensemble, created_blocks=created_blocks)
        # created_sequence.sampling_information = dict()

        created_sequences.append(created_sequence)

        return created_blocks, created_ensembles, created_sequences
