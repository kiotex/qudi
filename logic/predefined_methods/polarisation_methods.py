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


from logic.pulse_objects import PulseBlockElement
from logic.pulse_objects import PulseBlock
from logic.pulse_objects import PulseBlockEnsemble
from logic.pulse_objects import PulseSequence
import numpy as np


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

def generate_KDDxy_polarising_sequence(self, name='KDDxy_pol_seq', rabi_period=200e-9, mw_freq=100e+6, mw_amp=0.25,
                              start_tau=0.5e-6, incr_tau=1.0e-9, num_of_points=20, kdd_order=4,
                              mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=1.0, delay_length=0.7e-6,
                              wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2',
                              alternating=True):

    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get tau array for measurement ticks
    tau_array = start_tau + np.arange(num_of_points) * incr_tau

    # create the static waveform elements
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp, gate_count_channel)
    readout = waveform(self, [laser_element, delay_element, waiting_element], 'READOUT')

    # get pihalf x element
    pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0, gate_count_channel)
    pihalf_x = waveform(self, [pihalf_x_element], 'PI_HALF_X')

    # get pihalf y element
    pihalf_y_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 90.0,
                                            gate_count_channel)
    pihalf_y = waveform(self, [pihalf_y_element], 'PI_HALF_Y')

    # get -x pihalf (3pihalf) element
    pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180., gate_count_channel)
    pi3half = waveform(self, [pi3half_element], 'PI_3_HALF')

    # get pi_x element
    pi_0_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0, gate_count_channel)

    # get pi_30 element
    pi_30_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 30.0,
                                        gate_count_channel)

    # get pi_y element
    pi_90_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 90.0, gate_count_channel)

    # get pi_120 element
    pi_120_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 120.0,
                                         gate_count_channel)

    # get pi_minus_x element
    pi_180_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 180.0,
                                        gate_count_channel)
    # Create sequence
    mainsequence_list = []
    i = 0

    for t in tau_array:
        subsequence_list = []

        # get tau half element
        tauhalf_element = self._get_idle_element(t/2 - 3*rabi_period/8, 0.0, False, gate_count_channel)

        # get tau element
        tau_element = self._get_idle_element(t - rabi_period/2, 0.0, False, gate_count_channel)

        name1 = 'prep_%04i' % i
        prep = waveform(self, [pihalf_x_element, tauhalf_element], name1)

        wfm_list = []
        name2 = 'KDD_%02i' % i

        for j in range(kdd_order - 1):
            wfm_list.extend([pi_30_element, tau_element, pi_0_element, tau_element,
                             pi_90_element, tau_element, pi_0_element, tau_element, pi_30_element,
                             tau_element,
                             pi_120_element, tau_element, pi_90_element, tau_element, pi_180_element,
                             tau_element, pi_90_element, tau_element, pi_120_element, tau_element])

        decoupling = waveform(self, wfm_list, name2)
        name3 = 'last_dec_%02i' % i
        last = waveform(self,
                        [pi_30_element, tau_element, pi_0_element, tau_element,
                         pi_90_element, tau_element, pi_0_element, tau_element, pi_30_element,
                         tau_element,
                         pi_120_element, tau_element, pi_90_element, tau_element, pi_180_element,
                         tau_element, pi_90_element, tau_element, pi_120_element, tauhalf_element],
                        name3)

        name4 = 'INTER1_%04i' % i
        inter1 = waveform(self, [pihalf_y_element, tauhalf_element, tauhalf_element], name4)

        name5 = 'INTER2_%04i' % i
        inter2 = waveform(self, [tauhalf_element, pihalf_x_element], name5)

        subsequence_list.append((prep, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((last, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((inter1, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((last, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((inter2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        if alternating:
            name6 = 'INTER3_%04i' % i
            inter3 = waveform(self, [tauhalf_element, pi3half_element], name6)

            subsequence_list.append((prep, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((last, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((inter1, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((decoupling, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((last, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((inter3, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        i = i + 1

        mainsequence_list.extend(subsequence_list)

    sequence = PulseSequence(name=name, ensemble_param_list=mainsequence_list, rotating_frame=True)

    sequence.sample_rate = self.sample_rate
    sequence.activation_config = self.activation_config
    sequence.amplitude_dict = self.amplitude_dict
    sequence.laser_channel = self.laser_channel
    sequence.alternating = True
    sequence.laser_ignore_list = []

    self.save_sequence(name, sequence)
    print(sequence)
    return sequence

def generate_HHamp(self, name='HartmannHahn_amp', rabi_period=1.0e-6, spinlock_length=20e-6, mw_freq=0.1e+9,
                   pulse_amp=0.5, start_amp=0.05, incr_amp=0.01, num_of_points=50,
                   mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=1.0, delay_length=0.7e-6,
                   wait_time=1.0e-6, seq_trig_channel='', gate_count_channel='d_ch2'):
    """

    """
    # Sanity checks
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length,
                                                           channel_amp, gate_count_channel)
    # get pihalf element

    pihalf_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, pulse_amp,
                                          mw_freq, 0.0, gate_count_channel)
    # get 3pihalf element
    pi3half_element = self._get_mw_element(3 * rabi_period / 4, 0.0, mw_channel, False, pulse_amp,
                                           mw_freq, 0.0, gate_count_channel)

    if sync_trig_channel is not None:
        # get sequence trigger element
        seqtrig_element = self._get_trigger_element(20.0e-9, 0.0, sync_trig_channel,
                                                    amp=channel_amp)
        # Create its own block out of the element
        seq_block = PulseBlock('seq_trigger', [seqtrig_element])
        # save block
        self.save_block('seq_trigger', seq_block)

    # Create amplitude list array
    amp_array = start_amp + np.arange(num_of_points) * incr_amp

    # Create element list for HHamp PulseBlock
    element_list = []
    for sl_amp in amp_array:
        sl_element = self._get_mw_element(spinlock_length, 0.0, mw_channel, False, sl_amp, mw_freq,
                                          90.0)
        # actual alternating HH-amp sequence
        element_list.append(pihalf_element)
        element_list.append(sl_element)
        element_list.append(pihalf_element)
        element_list.append(laser_element)
        element_list.append(delay_element)
        element_list.append(waiting_element)

        element_list.append(pi3half_element)
        element_list.append(sl_element)
        element_list.append(pi3half_element)
        element_list.append(laser_element)
        element_list.append(delay_element)
        element_list.append(waiting_element)

    # Create PulseBlock object
    hhamp_block = PulseBlock(name, element_list)
    # save block
    self.save_block(name, hhamp_block)

    # Create Block list with repetitions and sequence trigger if needed.
    # remember number_of_taus=0 also counts as first round.
    block_list = [(hhamp_block, 0)]

    if sync_trig_channel is not None:
        block_list.append((seq_block, 0))

    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=True)
    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = True
    block_ensemble.laser_ignore_list = []
    block_ensemble.controlled_vals_array = amp_array
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_HHtau(self, name='HartmanhHahn_tau', rabi_period=200e-9, spinlock_amp=0.1, mw_freq=100e6,
                   mw_amp=0.25, start_tau=0.001, incr_tau=0.001, num_of_points=50,
                   mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
                    wait_time=1.0e-6, sync_trig_channel='', gate_count_channel=''):

    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length,
                                                           channel_amp, gate_count_channel)
    # get pihalf element

    pihalf_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                          mw_freq, 0.0, gate_count_channel)
    # get 3pihalf element
    pi3half_element = self._get_mw_element(3 * rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 0.0, gate_count_channel)

    # get spinlock element
    sl_element = self._get_mw_element(start_tau, incr_tau, mw_channel, True, spinlock_amp, mw_freq,
                                      90.0, gate_count_channel)

    if sync_trig_channel is not None:
        # get sequence trigger element
        seqtrig_element = self._get_trigger_element(20.0e-9, 0.0, sync_trig_channel,
                                                    amp=channel_amp)
        # Create its own block out of the element
        seq_block = PulseBlock('seq_trigger', [seqtrig_element])
        # save block
        self.save_block('seq_trigger', seq_block)

    # Create element list for HHamp PulseBlock
    element_list = []
    # actual alternating HH-amp sequence
    element_list.append(pihalf_element)
    element_list.append(sl_element)
    element_list.append(pihalf_element)
    element_list.append(laser_element)
    element_list.append(delay_element)
    element_list.append(waiting_element)

    element_list.append(pi3half_element)
    element_list.append(sl_element)
    element_list.append(pi3half_element)
    element_list.append(laser_element)
    element_list.append(delay_element)
    element_list.append(waiting_element)

    # Create PulseBlock object
    hhtau_block = PulseBlock(name, element_list)
    # save block
    self.save_block(name, hhtau_block)

    # Create Block list with repetitions and sequence trigger if needed.
    # remember number_of_taus=0 also counts as first round.
    block_list = [(hhtau_block, num_of_points-1)]
    if sync_trig_channel is not None:
        block_list.append((seq_block, 0))

    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=True)
    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = True
    block_ensemble.laser_ignore_list = []
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

# def generate_Hartmann_Hahn_tau_sequence(self, name='HHahn_tau_seq', rabi_period=200e-9, spinlock_amp=0.2, mw_freq=100e6,
#                    mw_amp=0.25, start_tau=30*1e-6, incr_tau=2*1e-6, num_of_points=50,
#                    mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
#                     wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2', alternating = True):
#
#     """
#
#     """
#     # Sanity checks
#     if gate_count_channel == '':
#         gate_count_channel = None
#     if sync_trig_channel == '':
#         sync_trig_channel = None
#     err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
#                                               gate_count_channel=gate_count_channel,
#                                               sync_trig_channel=sync_trig_channel)
#     if err_code != 0:
#         return
#
#     # get tau array for measurement ticks
#     tau_array = start_tau + np.arange(num_of_points) * incr_tau
#
#     # create the static waveform elements
#     # get waiting element
#     waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
#     # get laser and delay element
#     laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp,
#                                                            gate_count_channel)
#     readout = waveform(self, [laser_element, delay_element, waiting_element], 'READOUT')
#
#     # get pihalf x element
#     pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0,
#                                             gate_count_channel)
#     flip1 = waveform(self, [pihalf_x_element], 'FLIP1')
#     # get -x pihalf (3pihalf) element
#     pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
#                                            mw_freq, 180., gate_count_channel)
#     flip2 = waveform(self, [pi3half_element], 'FLIP2')
#     # Create sequence
#     mainsequence_list = []
#     i = 0
#
#     for t in tau_array:
#         subsequence_list = []
#
#         length =(1.0/mw_freq)*20
#         rep = int((t - rabi_period / 4)//length)
#         rest =(t - rabi_period / 4)-rep*length
#
#         # get spinlock element
#         sl_element1 = self._get_mw_element(length, 0.0, mw_channel, True, spinlock_amp, mw_freq,
#                                           90.0, gate_count_channel)
#         sl_element2 = self._get_mw_element(rest, 0.0, mw_channel, True, spinlock_amp, mw_freq,
#                                            90.0, gate_count_channel)
#         # make sequence waveform
#         name1 = 'LOCK_%04i' % i
#         name2 = 'REST_%04i' % i
#
#         lock = waveform(self, [sl_element1], name1)
#         rest = waveform(self, [sl_element2], name2)
#
#         subsequence_list.append((flip1, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#         subsequence_list.append((lock, {'repetitions': rep, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#         subsequence_list.append(
#             (rest, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#         subsequence_list.append((flip1, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#         subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#
#         if alternating:
#             subsequence_list.append((flip1, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#             subsequence_list.append(
#                 (lock, {'repetitions': rep, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#             subsequence_list.append(
#                 (rest, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#             subsequence_list.append((flip2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#             subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
#
#         i = i + 1
#
#         mainsequence_list.extend(subsequence_list)
#
#     sequence = PulseSequence(name=name, ensemble_param_list=mainsequence_list, rotating_frame=True)
#
#     sequence.sample_rate = self.sample_rate
#     sequence.activation_config = self.activation_config
#     sequence.amplitude_dict = self.amplitude_dict
#     sequence.laser_channel = self.laser_channel
#     sequence.alternating = True
#     sequence.laser_ignore_list = []
#
#     self.save_sequence(name, sequence)
#     print(sequence)
#     return sequence


def generate_Hartmann_Hahn_tau_sequence(self, name='HHtauseq', rabi_period=200e-9, spinlock_amp=0.2, mw_freq=100e6,
                   mw_amp=0.25, start_tau=30*1e-6, incr_tau=2*1e-6, num_of_points=50,
                   mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
                    wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2', alternating = True):

    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get tau array for measurement ticks
    tau_array = start_tau + np.arange(num_of_points) * incr_tau

    # create the static waveform elements
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp)
    # get pihalf x element
    pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0)
    last_pihalf_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0,
                                               gate_count_channel)
    # get -x pihalf (3pihalf) element
    pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180., gate_count_channel)
    # Create sequence
    mainsequence_list = []
    i = 0

    for t in tau_array:
        subsequence_list = []
        # get spinlock element
        sl_element = self._get_mw_element(t, 0.0, mw_channel, True, spinlock_amp, mw_freq,
                                       90.0)
        # make sequence waveform
        name1 = 'LOCK_%02i' % i
        lock = waveform(self, [pihalf_x_element, sl_element, last_pihalf_element, laser_element, delay_element, waiting_element], name1)
        subsequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        if alternating:
            name2 = 'LOCK2_%02i' % i
            lock = waveform(self, [pihalf_x_element, sl_element, pi3half_element, laser_element, delay_element,
                                   waiting_element], name2)
            subsequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        i = i + 1
        mainsequence_list.extend(subsequence_list)

    sequence = PulseSequence(name=name, ensemble_param_list=mainsequence_list, rotating_frame=True)

    sequence.sample_rate = self.sample_rate
    sequence.activation_config = self.activation_config
    sequence.amplitude_dict = self.amplitude_dict
    sequence.laser_channel = self.laser_channel
    sequence.alternating = True
    sequence.laser_ignore_list = []

    self.save_sequence(name, sequence)
    print(sequence)
    return sequence

def generate_HH_tau_waiting_sequence(self, name='HH_waiting', rabi_period=200e-9, spinlock_amp=0.2, mw_freq=100e6,
                   mw_amp=0.25, start_tau=30*1e-6, incr_tau=2*1e-6, num_of_points=25, lock_time=1.0e-6,
                   mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
                   wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2', alternating = True):

    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get tau array for measurement ticks
    tau_array = start_tau + np.arange(num_of_points) * incr_tau

    # create the static waveform elements
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp,
                                                           gate_count_channel)
    readout = waveform(self, [laser_element, delay_element, waiting_element], 'READOUT')

    init_element, delay2_element = self._get_laser_init_element(laser_length, 0.0, False, delay_length, channel_amp,
                                                                gate_count_channel)

    # get pihalf x element
    pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0,
                                            gate_count_channel)
    # flip1 = waveform(self, [pihalf_x_element], 'FLIP1')
    # get -x pihalf (3pihalf) element
    pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180., gate_count_channel)
    # flip2 = waveform(self, [pi3half_element], 'FLIP2')
    # Create sequence
    mainsequence_list = []
    i = 0

    # get spinlock element
    sl_element = self._get_mw_element(lock_time, 0.0, mw_channel, True, spinlock_amp, mw_freq,
                                       90.0, gate_count_channel)

    for t in tau_array:
        subsequence_list = []

        # make sequence waveform
        name1 = 'LOCK_%03i' % i

        idle_element = self._get_idle_element(t, 0.0, False, gate_count_channel)

        lock = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element, pihalf_x_element, laser_element, delay_element,
                               waiting_element, idle_element], name1)

        subsequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        if alternating:
            name2 = 'LOCK2_%03i' % i
            lock2 = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element, pi3half_element, laser_element, delay_element,
                                    waiting_element, idle_element], name2)
            subsequence_list.append((lock2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        i = i + 1

        mainsequence_list.extend(subsequence_list)

    sequence = PulseSequence(name=name, ensemble_param_list=mainsequence_list, rotating_frame=True)

    sequence.sample_rate = self.sample_rate
    sequence.activation_config = self.activation_config
    sequence.amplitude_dict = self.amplitude_dict
    sequence.laser_channel = self.laser_channel
    sequence.alternating = True
    sequence.laser_ignore_list = []

    self.save_sequence(name, sequence)
    print(sequence)
    return sequence


def generate_HH_fixed_waiting(self, name='HH_fix_wait', rabi_period=200e-9, spinlock_amp=0.2, mw_freq=100e6,
                   mw_amp=0.25, start_tau=30*1e-6, incr_tau=2*1e-6, num_of_points=25, idle_time=1.0e-6,
                   mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
                   wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2', alternating = True):

    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get tau array for measurement ticks
    tau_array = start_tau + np.arange(num_of_points) * incr_tau

    # create the static waveform elements
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp,
                                                           gate_count_channel)
    readout = waveform(self, [laser_element, delay_element, waiting_element], 'READOUT')

    init_element, delay2_element = self._get_laser_init_element(laser_length, 0.0, False, delay_length, channel_amp,
                                                                gate_count_channel)

    # get pihalf x element
    pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0,
                                            gate_count_channel)
    # flip1 = waveform(self, [pihalf_x_element], 'FLIP1')
    # get -x pihalf (3pihalf) element
    pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180., gate_count_channel)
    # flip2 = waveform(self, [pi3half_element], 'FLIP2')
    # Create sequence
    mainsequence_list = []
    i = 0

    idle_element = self._get_idle_element(idle_time, 0.0, False, gate_count_channel)

    for t in tau_array:
        subsequence_list = []

        # make sequence waveform
        name1 = 'LOCK_%03i' % i

        # get spinlock element
        sl_element = self._get_mw_element(t, 0.0, mw_channel, True, spinlock_amp, mw_freq,
                                          90.0, gate_count_channel)

        lock = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element, pihalf_x_element, laser_element, delay_element,
                               waiting_element, idle_element], name1)

        subsequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        if alternating:
            name2 = 'LOCK2_%03i' % i
            lock2 = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element, pi3half_element, laser_element, delay_element,
                                    waiting_element, idle_element], name2)
            subsequence_list.append((lock2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        i = i + 1

        mainsequence_list.extend(subsequence_list)

    sequence = PulseSequence(name=name, ensemble_param_list=mainsequence_list, rotating_frame=True)

    sequence.sample_rate = self.sample_rate
    sequence.activation_config = self.activation_config
    sequence.amplitude_dict = self.amplitude_dict
    sequence.laser_channel = self.laser_channel
    sequence.alternating = True
    sequence.laser_ignore_list = []

    self.save_sequence(name, sequence)
    print(sequence)
    return sequence

def generate_HH_SMART_waiting(self, name='HHSMWAIT', rabi_period=200e-9, spinlock_amp=0.2, mw_freq=100e6,
                   mw_amp=0.25, tau=2*1e-6, lock_time=100.0*1e-6,
                   mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
                   wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2', alternating = True):

    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # create the static waveform elements
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp,
                                                           gate_count_channel)
    init_element, delay2_element = self._get_laser_init_element(laser_length, 0.0, False, delay_length, channel_amp,
                                                                gate_count_channel)
    # get pihalf x element
    pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0,
                                            gate_count_channel)
    # get -x pihalf (3pihalf) element
    pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180., gate_count_channel)
    # Create sequence
    mainsequence_list = []
    subsequence_list = []

    # get spinlock element
    sl_element = self._get_mw_element(lock_time, 0.0, mw_channel, True, spinlock_amp, mw_freq,
                                       90.0, gate_count_channel)

    idle_element = self._get_idle_element(tau, 0.0, False, gate_count_channel)

    lock = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element, pihalf_x_element, laser_element, delay_element,
                               waiting_element, idle_element], 'Lock')

    subsequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

    lock2 = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element, pi3half_element, laser_element, delay_element,
                                    waiting_element, idle_element], 'Lock2')
    subsequence_list.append((lock2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

    mainsequence_list.extend(subsequence_list)

    sequence = PulseSequence(name=name, ensemble_param_list=mainsequence_list, rotating_frame=True)

    sequence.sample_rate = self.sample_rate
    sequence.activation_config = self.activation_config
    sequence.amplitude_dict = self.amplitude_dict
    sequence.laser_channel = self.laser_channel
    sequence.alternating = True
    sequence.laser_ignore_list = []

    self.save_sequence(name, sequence)
    print(sequence)
    return sequence

def generate_HHpol(self, name='HartmannHahn_pol', rabi_period=200e-9, spinlock_length=20.0e-6,
                   spinlock_amp=0.1, mw_freq=0.1e+9, pulse_amp=0.25, polarization_steps=50,
                   mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=1.0, delay_length=0.7e-6,
                   wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2'):
    """

    """
    # Sanity checks
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)

    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length,
                                                           channel_amp, gate_count_channel)
    # get pihalf element

    pihalf_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, pulse_amp,
                                          mw_freq, 0.0, gate_count_channel)
    # get 3pihalf element
    pi3half_element = self._get_mw_element(3 * rabi_period / 4, 0.0, mw_channel, False, pulse_amp,
                                           mw_freq, 0.0, gate_count_channel)
    # get spinlock element
    sl_element = self._get_mw_element(spinlock_length, 0.0, mw_channel, False, spinlock_amp,
                                      mw_freq, 90.0, gate_count_channel)

    if sync_trig_channel is not None:
        # get sequence trigger element
        seqtrig_element = self._get_trigger_element(20.0e-9, 0.0, sync_trig_channel,
                                                    amp=channel_amp)
        # Create its own block out of the element
        seq_block = PulseBlock('seq_trigger', [seqtrig_element])
        # save block
        self.save_block('seq_trigger', seq_block)

    # create the pulse block for "up"-polarization
    element_list = []
    # actual HH-pol sequence
    element_list.append(pihalf_element)
    element_list.append(sl_element)
    element_list.append(pihalf_element)
    element_list.append(laser_element)
    element_list.append(delay_element)
    element_list.append(waiting_element)

    HHpolup_block = PulseBlock(name + '_up', element_list)
    self.save_block(name + '_up', HHpolup_block)

    # create the pulse block for "down"-polarization
    element_list = []
    # actual HH-pol sequence
    element_list.append(pi3half_element)
    element_list.append(sl_element)
    element_list.append(pi3half_element)
    element_list.append(laser_element)
    element_list.append(delay_element)
    element_list.append(waiting_element)

    HHpoldown_block = PulseBlock(name + '_down', element_list)
    self.save_block(name + '_down', HHpoldown_block)

    # Create Block list with repetitions and sequence trigger if needed
    # remember number_of_taus=0 also counts as first round
    block_list = [(HHpolup_block, polarization_steps - 1),
                  (HHpoldown_block, polarization_steps - 1)]
    if sync_trig_channel:
        block_list.append((seq_block, 0))

    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=True)
    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = False
    block_ensemble.laser_ignore_list = []
    block_ensemble.controlled_vals_array = np.arange(1, 2 * polarization_steps + 1)
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_PulsePol_sequence(self, name='PulsePol_sequence', rabi_period=200e-9, mw_freq=100e+6, mw_amp=0.25,
                              start_tau=0.5e-6, incr_tau=0.01e-6, num_of_points=20, repetitions=239,
                              mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
                              wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2',
                              alternating=True):

    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get tau array for measurement ticks
    tau_array = start_tau + np.arange(num_of_points) * incr_tau

    # create the static waveform elements
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp, gate_count_channel)
    readout = waveform(self, [laser_element, delay_element, waiting_element], 'READOUT')

    # get pihalf x element
    pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0, gate_count_channel)

    # get pihalf y element
    pihalf_y_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 90.0,
                                            gate_count_channel)

    # get pi_x element
    pi_x_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0, gate_count_channel)

    # get pi_y element
    pi_y_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 90.0, gate_count_channel)

    # get pi_minus_x element
    pi_minus_x_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 180.0,
                                        gate_count_channel)

    # get -x pihalf (3pihalf) element
    pi3half_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180., gate_count_channel)

    # Create sequence
    mainsequence_list = []
    i = 0

    for t in tau_array:
        subsequence_list = []

        # get tau element
        tau_element = self._get_idle_element(t - rabi_period/2, 0.0, False, gate_count_channel)

        if repetitions <= 20:

            wfm_list = []
            name1 = 'pol_step1_%04i' % i

            for j in range(repetitions):
                wfm_list.extend([pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                            pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element,
                                            pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                            pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element
                                           ])

            #make sequence waveform
            polarisation = waveform(self, wfm_list, name1)

            subsequence_list.append((polarisation, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        else:

            num1 = repetitions // 20
            num2 = repetitions - num1*20

            for k in range(num1):

                wfm_list = []
                name1 = 'pol_step_%02i' % i + 'N_%02i' % k

                for j in range(20):
                    wfm_list.extend([pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                     pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element,
                                     pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                     pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element
                                     ])
                    # make sequence waveform
                polarisation = waveform(self, wfm_list, name1)
                subsequence_list.append(
                    (polarisation, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            wfm_list = []
            name2 = 'pol_step2_%02i' % i + 'N_%02i' % (k+1)

            for j in range(num2):
                wfm_list.extend([pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                 pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element,
                                 pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                 pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element
                                 ])
                # make sequence waveform
            polarisation = waveform(self, wfm_list, name2)
            subsequence_list.append(
                (polarisation, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        if alternating:
            if repetitions <= 20:

                wfm_list = []
                name3 = 'pol_step2_%04i' % i

                for j in range(repetitions-1):
                    wfm_list.extend([pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                     pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element,
                                     pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                     pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element
                                     ])

                wfm_list.extend([pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                 pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element,
                                 pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                 pihalf_x_element, tau_element, pi_y_element, tau_element, pi3half_x_element
                                 ])
                    # make sequence waveform
                polarisation = waveform(self, wfm_list, name3)

                subsequence_list.append(
                    (polarisation, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            else:

                num1 = repetitions // 20
                num2 = repetitions - num1*20

                for k in range(num1):

                    wfm_list = []
                    name3 = 'pol_step2_%02i' % i + 'N_%02i' % k

                    for j in range(20):
                        wfm_list.extend(
                            [pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                             pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element,
                             pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                             pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element
                             ])
                        # make sequence waveform
                    polarisation = waveform(self, wfm_list, name3)
                    subsequence_list.append(
                        (polarisation, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

                wfm_list = []
                name4 = 'pol_step3_%02i' % i + 'N_%02i' % (k + 1)

                for j in range(num2-1):
                    wfm_list.extend([pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                     pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element,
                                     pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                     pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element
                                     ])
                wfm_list.extend([pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                 pihalf_x_element, tau_element, pi_y_element, tau_element, pihalf_x_element,
                                 pihalf_y_element, tau_element, pi_minus_x_element, tau_element, pihalf_y_element,
                                 pihalf_x_element, tau_element, pi_y_element, tau_element, pi3half_x_element
                                 ])
                    # make sequence waveform
                polarisation = waveform(self, wfm_list, name4)
                subsequence_list.append(
                    (polarisation, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        i = i + 1

        mainsequence_list.extend(subsequence_list)

    sequence = PulseSequence(name=name, ensemble_param_list=mainsequence_list, rotating_frame=True)

    sequence.sample_rate = self.sample_rate
    sequence.activation_config = self.activation_config
    sequence.amplitude_dict = self.amplitude_dict
    sequence.laser_channel = self.laser_channel
    sequence.alternating = True
    sequence.laser_ignore_list = []

    self.save_sequence(name, sequence)
    print(sequence)
    return sequence


def generate_HH_amp_sweep_sequence(self, name='HH_amp_sweep', rabi_period=200e-9, spinlock_amp_start=0.12,
                                   spinlock_amp_end=0.095, mw_freq=100e6, mw_amp=0.25, tau=30*1e-6, num_of_points=100,
                                    mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
                               wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2', alternating = True):

    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get tau array for measurement ticks
    mw_array = np.linspace(spinlock_amp_start, spinlock_amp_end, num_of_points)

    # create the static waveform elements
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp)
    readout = waveform(self, [laser_element, delay_element, waiting_element], 'READOUT')

    # get pihalf x element
    pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0)
    last_pihalf_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0,
                                               gate_count_channel)
    # get -x pihalf (3pihalf) element
    pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180., gate_count_channel)
    # Create sequence
    mainsequence_list = []
    i = 0

    for spinlock_amp in mw_array:
        subsequence_list = []

        # get spinlock element
        sl_element = self._get_mw_element(tau, 0.0, mw_channel, True, spinlock_amp, mw_freq, 90.0)
        name1 = 'LOCK%03i' % i
        lock = waveform(self, [pihalf_x_element, sl_element, last_pihalf_element], name1)

        subsequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        if alternating:
            name2 = 'LOCK2%03i' % i
            lock2 = waveform(self, [pihalf_x_element, sl_element, pi3half_element], name2)

            subsequence_list.append((lock2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        i = i + 1

        mainsequence_list.extend(subsequence_list)

    sequence = PulseSequence(name=name, ensemble_param_list=mainsequence_list, rotating_frame=True)

    sequence.sample_rate = self.sample_rate
    sequence.activation_config = self.activation_config
    sequence.amplitude_dict = self.amplitude_dict
    sequence.laser_channel = self.laser_channel
    sequence.alternating = True
    sequence.laser_ignore_list = []

    self.save_sequence(name, sequence)
    print(sequence)
    return sequence


def generate_HH_polarization_build_up(self, name='pol_buildup', rabi_period=200e-9, spinlock_amp=0.2, mw_freq=100e6,
                   mw_amp=0.25, start_tau=30*1e-6, incr_tau=2*1e-6, num_of_points=50, full_time = 100.0*1e-6,
                   mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
                    wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2', alternating = True):

    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    # get tau array for measurement ticks
    tau_array = start_tau + np.arange(num_of_points) * incr_tau

    # create the static waveform elements
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp,
                                                           gate_count_channel)
    readout = waveform(self, [laser_element, delay_element, waiting_element], 'READOUT')

    init_element, delay2_element = self._get_laser_init_element(laser_length, 0.0, False, delay_length, channel_amp,
                                                                gate_count_channel)

    # get pihalf x element
    pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0,
                                            gate_count_channel)
    # flip1 = waveform(self, [pihalf_x_element], 'FLIP1')
    # get -x pihalf (3pihalf) element
    pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180., gate_count_channel)
    # flip2 = waveform(self, [pi3half_element], 'FLIP2')
    # Create sequence
    mainsequence_list = []
    i = 0

    for t in tau_array:
        subsequence_list = []

        # get spinlock element
        sl_element1 = self._get_mw_element(t, 0.0, mw_channel, True, spinlock_amp, mw_freq,
                                          90.0, gate_count_channel)
        # make sequence waveform
        name1 = 'LOCK_%03i' % i

        idle_element = self._get_idle_element(full_time - t, 0.0, False, gate_count_channel)

        lock = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element1, pihalf_x_element, laser_element, delay_element, waiting_element, idle_element], name1)

        subsequence_list.append((lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        if alternating:

            name2 = 'LOCK2_%03i' % i
            lock2 = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element1, pi3half_element, laser_element, delay_element, waiting_element, idle_element], name2)
            subsequence_list.append((lock2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        i = i + 1

        mainsequence_list.extend(subsequence_list)

    sequence = PulseSequence(name=name, ensemble_param_list=mainsequence_list, rotating_frame=True)

    sequence.sample_rate = self.sample_rate
    sequence.activation_config = self.activation_config
    sequence.amplitude_dict = self.amplitude_dict
    sequence.laser_channel = self.laser_channel
    sequence.alternating = True
    sequence.laser_ignore_list = []

    self.save_sequence(name, sequence)
    print(sequence)
    return sequence


def generate_PROPI(self, name='propi', rabi_period=200e-9, spinlock_amp=0.2, mw_freq=100e6, mw_amp=0.25, tau=30*1e-6,
                   N = 50, M = 50, step_M = 1, mw_channel='a_ch1', laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6,
                   wait_time=1.0e-6, sync_trig_channel='', gate_count_channel='d_ch2', alternating = True):
    """

    """
    # Sanity checks
    if gate_count_channel == '':
        gate_count_channel = None
    if sync_trig_channel == '':
        sync_trig_channel = None
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel,
                                              gate_count_channel=gate_count_channel,
                                              sync_trig_channel=sync_trig_channel)
    if err_code != 0:
        return

    m = np.arange(1, M+1, step_M)

    # create the static waveform elements
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length, channel_amp)
    init_element, delay2_element = self._get_laser_init_element(laser_length, 0.0, False, delay_length, channel_amp)

    # get pihalf x element
    pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0)
    last_pihalf_x_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0,
                                                 gate_count_channel)

    # get -x pihalf (3pihalf) element
    pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180.)
    last_pi3half_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 180., gate_count_channel)
    # Create sequence

    sl_element = self._get_mw_element(tau, 0.0, mw_channel, False, spinlock_amp, mw_freq, 90.0)
    lock = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element,
                           pihalf_x_element], 'lock_up')
    last_lock = waveform(self, [init_element, delay2_element, waiting_element, pihalf_x_element, sl_element,
                           last_pihalf_x_element], 'last_lock')
    repolarization = waveform(self, [init_element, delay2_element, waiting_element,
                                     pi3half_element, sl_element, pihalf_x_element], 'repol_up')
    last_repolarization = waveform(self, [laser_element, delay_element, waiting_element,
                                     pi3half_element, sl_element, last_pihalf_x_element], 'repol_up2')

    repolarization2 = waveform(self, [init_element, delay2_element, waiting_element, waiting_element,
                                      pi3half_element, sl_element, pi3half_element], 'repol_down')

    last_repolarization2 = waveform(self, [laser_element, delay_element, waiting_element,
                                      pi3half_element, sl_element, last_pi3half_element], 'repol_down2')



    last_repolarization3 = waveform(self, [laser_element, delay_element, waiting_element,
                                          pi3half_element, sl_element, pihalf_x_element], 'repol_up3')
    last_repolarization4 = waveform(self, [laser_element, delay_element, waiting_element,
                                           pi3half_element, sl_element, pi3half_element], 'repol_down3')

    subsequence_list = []
    # make sequence waveform

    if step_M==1:

        subsequence_list.append((lock, {'repetitions': N-1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((last_lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
        subsequence_list.append((last_repolarization3, {'repetitions': M, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        if alternating:

            subsequence_list.append((lock, {'repetitions': N - 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((last_lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((last_repolarization4, {'repetitions': M, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

    else:

        for j in m:

            if j==1:
                j=2

            subsequence_list.append((lock, {'repetitions': N - 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((last_lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append(
                (repolarization, {'repetitions': int(j-1), 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append(
                (last_repolarization3, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            if alternating:
                subsequence_list.append(
                    (lock, {'repetitions': N - 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
                subsequence_list.append(
                    (last_lock, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
                subsequence_list.append(
                    (repolarization2, {'repetitions': int(j-1), 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
                subsequence_list.append(
                    (last_repolarization4, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

    sequence = PulseSequence(name=name, ensemble_param_list=subsequence_list, rotating_frame=True)

    sequence.sample_rate = self.sample_rate
    sequence.activation_config = self.activation_config
    sequence.amplitude_dict = self.amplitude_dict
    sequence.laser_channel = self.laser_channel
    sequence.alternating = True
    sequence.laser_ignore_list = []

    self.save_sequence(name, sequence)
    print(sequence)
    return sequence

####################################################################################################
#                                   Helper methods                                              ####
####################################################################################################
def _get_channel_lists(self):
    """
    @return: two lists with the names of digital and analog channels
    """
    # split digital and analogue channels
    digital_channels = [chnl for chnl in self.activation_config if 'd_ch' in chnl]
    analog_channels = [chnl for chnl in self.activation_config if 'a_ch' in chnl]
    return digital_channels, analog_channels

def _get_idle_element(self, length, increment, use_as_tick, gate_count_chnl=None):
    """
    Creates an idle pulse PulseBlockElement

    @param float length: idle duration in seconds
    @param float increment: idle duration increment in seconds
    @param bool use_as_tick: use as tick flag of the PulseBlockElement

    @return: PulseBlockElement, the generated idle element
    """
    # get channel lists
    digital_channels, analog_channels = self._get_channel_lists()

    # input params for MW element generation
    idle_params = [{}] * self.analog_channels
    idle_digital = [False] * self.digital_channels
    idle_function = ['Idle'] * self.analog_channels

    if gate_count_chnl is not None:
        # Determine analogue or digital gate trigger and set parameters accordingly.
        if 'd_ch' in gate_count_chnl:
            gate_index = digital_channels.index(gate_count_chnl)
            idle_digital[gate_index] = True

    # Create idle element
    idle_element = PulseBlockElement(init_length_s=length, increment_s=increment,
                                     pulse_function=idle_function, digital_high=idle_digital,
                                     parameters=idle_params, use_as_tick=use_as_tick)
    return idle_element


def _get_trigger_element(self, length, increment, channel, use_as_tick=False, amp=None):
    """
    Creates a trigger PulseBlockElement

    @param float length: trigger duration in seconds
    @param float increment: trigger duration increment in seconds
    @param string channel: The pulser channel to be triggered.
    @param bool use_as_tick: use as tick flag of the PulseBlockElement
    @param float amp: analog amplitude in case of analog channel in V

    @return: PulseBlockElement, the generated trigger element
    """
    # get channel lists
    digital_channels, analog_channels = self._get_channel_lists()

    # input params for trigger element generation
    trig_params = [{}] * self.analog_channels
    trig_digital = [False] * self.digital_channels
    trig_function = ['Idle'] * self.analog_channels

    # Determine analogue or digital trigger channel and set parameters accordingly.
    if 'd_ch' in channel:
        trig_index = digital_channels.index(channel)
        trig_digital[trig_index] = True
    elif 'a_ch' in channel:
        trig_index = analog_channels.index(channel)
        trig_function[trig_index] = 'DC'
        trig_params[trig_index] = {'amplitude1': amp}

    # Create trigger element
    trig_element = PulseBlockElement(init_length_s=length, increment_s=increment,
                                     pulse_function=trig_function, digital_high=trig_digital,
                                     parameters=trig_params, use_as_tick=use_as_tick)
    return trig_element

def _get_laser_element(self, length, increment, use_as_tick, delay_time=None, amp_V=None,
                       gate_count_chnl=None):
    """
    Creates laser and gate trigger PulseBlockElements

    @param float length: laser pulse duration in seconds
    @param float increment: laser pulse duration increment in seconds
    @param bool use_as_tick: use as tick flag of the PulseBlockElement
    @param float delay_time: (aom-) delay after the laser trigger in seconds
                             (only for gated fast counter)
    @param float amp_V: Analog voltage for laser and gate trigger (if those channels are analog)
    @param string gate_count_chnl: the channel descriptor string for the gate trigger

    @return: PulseBlockElement, two elements for laser and gate trigger (delay element)
    """
    # get channel lists
    digital_channels, analog_channels = self._get_channel_lists()

    # input params for laser element generation
    laser_params = [{}] * self.analog_channels
    laser_digital = [False] * self.digital_channels
    laser_function = ['Idle'] * self.analog_channels
    # input params for delay element generation (for gated fast counter)
    delay_params = [{}] * self.analog_channels
    delay_digital = [False] * self.digital_channels
    delay_function = ['Idle'] * self.analog_channels

    # Determine analogue or digital laser channel and set parameters accordingly.
    if 'd_ch' in self.laser_channel:
        laser_index = digital_channels.index(self.laser_channel)
        laser_digital[laser_index] = True
        laser_digital[digital_channels.index('d_ch3')] = True
    elif 'a_ch' in self.laser_channel:
        laser_index = analog_channels.index(self.laser_channel)
        laser_function[laser_index] = 'DC'
        laser_params[laser_index] = {'amplitude1': amp_V}
    # add gate trigger for gated fast counters
    if gate_count_chnl is not None:
        # Determine analogue or digital gate trigger and set parameters accordingly.
        if 'd_ch' in gate_count_chnl:
            gate_index = digital_channels.index(gate_count_chnl)
            laser_digital[gate_index] = False
            delay_digital[gate_index] = True
        elif 'a_ch' in gate_count_chnl:
            gate_index = analog_channels.index(gate_count_chnl)
            laser_function[gate_index] = 'DC'
            laser_params[gate_index] = {'amplitude1': amp_V}
            delay_function[gate_index] = 'DC'
            delay_params[gate_index] = {'amplitude1': amp_V}

    # Create laser element
    laser_element = PulseBlockElement(init_length_s=length, increment_s=increment,
                                      pulse_function=laser_function, digital_high=laser_digital,
                                      parameters=laser_params, use_as_tick=use_as_tick)
    # Create delay element
    delay_element = PulseBlockElement(init_length_s=delay_time, increment_s=0.0,
                                      pulse_function=delay_function, digital_high=delay_digital,
                                      parameters=delay_params, use_as_tick=use_as_tick)
    return laser_element, delay_element


def _get_laser_init_element(self, length, increment, use_as_tick, delay_time=None, amp_V=None,
                       gate_count_chnl=None):
    """
    Creates laser and gate trigger PulseBlockElements

    @param float length: laser pulse duration in seconds
    @param float increment: laser pulse duration increment in seconds
    @param bool use_as_tick: use as tick flag of the PulseBlockElement
    @param float delay_time: (aom-) delay after the laser trigger in seconds
                             (only for gated fast counter)
    @param float amp_V: Analog voltage for laser and gate trigger (if those channels are analog)
    @param string gate_count_chnl: the channel descriptor string for the gate trigger

    @return: PulseBlockElement, two elements for laser and gate trigger (delay element)
    """
    # get channel lists
    digital_channels, analog_channels = self._get_channel_lists()

    # input params for laser element generation
    laser_params = [{}] * self.analog_channels
    laser_digital = [False] * self.digital_channels
    laser_function = ['Idle'] * self.analog_channels
    # input params for delay element generation (for gated fast counter)
    delay_params = [{}] * self.analog_channels
    delay_digital = [False] * self.digital_channels
    delay_function = ['Idle'] * self.analog_channels

    # Determine analogue or digital laser channel and set parameters accordingly.
    if 'd_ch' in self.laser_channel:
        laser_index = digital_channels.index(self.laser_channel)
        laser_digital[laser_index] = True
    elif 'a_ch' in self.laser_channel:
        laser_index = analog_channels.index(self.laser_channel)
        laser_function[laser_index] = 'DC'
        laser_params[laser_index] = {'amplitude1': amp_V}
    # add gate trigger for gated fast counters
    if gate_count_chnl is not None:
        # Determine analogue or digital gate trigger and set parameters accordingly.
        if 'd_ch' in gate_count_chnl:
            gate_index = digital_channels.index(gate_count_chnl)
            laser_digital[gate_index] = True
            delay_digital[gate_index] = True
        elif 'a_ch' in gate_count_chnl:
            gate_index = analog_channels.index(gate_count_chnl)
            laser_function[gate_index] = 'DC'
            laser_params[gate_index] = {'amplitude1': amp_V}
            delay_function[gate_index] = 'DC'
            delay_params[gate_index] = {'amplitude1': amp_V}

    # Create laser element
    laser_element = PulseBlockElement(init_length_s=length, increment_s=increment,
                                      pulse_function=laser_function, digital_high=laser_digital,
                                      parameters=laser_params, use_as_tick=use_as_tick)
    # Create delay element
    delay_element = PulseBlockElement(init_length_s=delay_time, increment_s=0.0,
                                      pulse_function=delay_function, digital_high=delay_digital,
                                      parameters=delay_params, use_as_tick=use_as_tick)
    return laser_element, delay_element


def _get_mw_element(self, length, increment, mw_channel, use_as_tick, amp=None, freq=None,
                    phase=None, gate_count_chnl=None):
    """
    Creates a MW pulse PulseBlockElement

    @param float length: MW pulse duration in seconds
    @param float increment: MW pulse duration increment in seconds
    @param string mw_channel: The pulser channel controlling the MW. If set to 'd_chX' this will be
                              interpreted as trigger for an external microwave source. If set to
                              'a_chX' the pulser (AWG) will act as microwave source.
    @param bool use_as_tick: use as tick flag of the PulseBlockElement
    @param float freq: MW frequency in case of analogue MW channel in Hz
    @param float amp: MW amplitude in case of analogue MW channel in V
    @param float phase: MW phase in case of analogue MW channel in deg

    @return: PulseBlockElement, the generated MW element
    """
    # get channel lists
    digital_channels, analog_channels = self._get_channel_lists()

    # input params for MW element generation
    mw_params = [{}] * self.analog_channels
    mw_digital = [False] * self.digital_channels
    mw_function = ['Idle'] * self.analog_channels

    # Determine analogue or digital MW channel and set parameters accordingly.
    if 'd_ch' in mw_channel:
        mw_index = digital_channels.index(mw_channel)
        mw_digital[mw_index] = True
    elif 'a_ch' in mw_channel:
        mw_index = analog_channels.index(mw_channel)
        mw_function[mw_index] = 'Sin'
        mw_params[mw_index] = {'amplitude1': amp, 'frequency1': freq, 'phase1': phase}

    if gate_count_chnl is not None:
        # Determine analogue or digital gate trigger and set parameters accordingly.
        if 'd_ch' in gate_count_chnl:
            gate_index = digital_channels.index(gate_count_chnl)
            mw_digital[gate_index] = True
        # elif 'a_ch' in gate_count_chnl:
        #     gate_index = analog_channels.index(gate_count_chnl)
        #     laser_function[gate_index] = 'DC'
        #     laser_params[gate_index] = {'amplitude1': amp_V}
        #     delay_function[gate_index] = 'DC'
        #     delay_params[gate_index] = {'amplitude1': amp_V}

    # Create MW element
    mw_element = PulseBlockElement(init_length_s=length, increment_s=increment,
                                   pulse_function=mw_function, digital_high=mw_digital,
                                   parameters=mw_params, use_as_tick=use_as_tick)
    return mw_element

def _get_multiple_mw_element(self, length, increment, mw_channel, use_as_tick, amps = None,
                             freqs = None, phases = None):
    """
    Creates at the moment double or triple mw element. Is easily extended when further methods are developed in the
    module sampling_functions.

    @param float length: MW pulse duration in seconds
    @param float increment: MW pulse duration increment in seconds
    @param string mw_channel: The pulser channel controlling the MW. If set to 'd_chX' this will be
                              interpreted as trigger for an external microwave source. If set to
                              'a_chX' the pulser (AWG) will act as microwave source.
    @param bool use_as_tick: use as tick flag of the PulseBlockElement
    @param amps: list containing the amplitudes
    @param freqs: list containing the frequencies
    @param phases: list containing the phases
    @return: PulseBlockElement, the generated MW element
    """

    # some check if all the parameter lists have the same length
    set1 = set([len(amps), len(freqs), len(phases)])
    if len(set1) != 1:
        self.log.warning('the lists amps, freqs and phases should have same length')
    # get channel lists
    digital_channels, analog_channels = self._get_channel_lists()
    # supported sine methods at the moment
    prefix = ['Double', 'Triple']

    # check if the list lengths are in the supported range
    # and find out the method needed in this specific case

    list_len = [i for i in set1][0]
    if (list_len - 2 < 0) | (list_len - 2 > 1):
        self.log.warning('the length of your parameter lists is not supported')
    cur_prefix = prefix[list_len - 2]

    # input params for MW element generation
    mw_params = [{}] * self.analog_channels
    mw_digital = [False] * self.digital_channels
    mw_function = ['Idle'] * self.analog_channels

    param_bare = ['amplitude', 'frequency', 'phase']

    pre_settings = {param_bare[0]: amps, param_bare[1]: freqs, param_bare[2]: phases}
    settings= {}

    for key in pre_settings:
        for ii, val in enumerate(pre_settings[key]):
            settings[key + str(ii+1)] = val


    # Determine analogue or digital MW channel and set parameters accordingly.
    if 'd_ch' in mw_channel:
        self.log.warning('for multiple_mw_element only pulser can be used')
    elif 'a_ch' in mw_channel:
        mw_index = analog_channels.index(mw_channel)
        mw_function[mw_index] = cur_prefix + 'Sin'
        mw_params[mw_index] = settings

    # Create MW element
    multiple_mw_element = PulseBlockElement(init_length_s=length, increment_s=increment,
                                   pulse_function=mw_function, digital_high=mw_digital,
                                   parameters=mw_params, use_as_tick=use_as_tick)
    return multiple_mw_element

def _get_mw_laser_element(self, length, increment, mw_channel, use_as_tick, delay_time=None,
                          laser_amp=None, mw_amp=None, mw_freq=None, mw_phase=None,
                          gate_count_chnl=None):
    """

    @param length:
    @param increment:
    @param mw_channel:
    @param use_as_tick:
    @param delay_time:
    @param laser_amp:
    @param mw_amp:
    @param mw_freq:
    @param mw_phase:
    @param gate_count_chnl:
    @return:
    """
    # get channel lists
    digital_channels, analog_channels = self._get_channel_lists()

    # input params for laser/mw element generation
    laser_mw_params = [{}] * self.analog_channels
    laser_mw_digital = [False] * self.digital_channels
    laser_mw_function = ['Idle'] * self.analog_channels
    # input params for delay element generation (for gated fast counter)
    delay_params = [{}] * self.analog_channels
    delay_digital = [False] * self.digital_channels
    delay_function = ['Idle'] * self.analog_channels

    # Determine analogue or digital laser channel and set parameters accordingly.
    if 'd_ch' in self.laser_channel:
        laser_index = digital_channels.index(self.laser_channel)
        laser_mw_digital[laser_index] = True
    elif 'a_ch' in self.laser_channel:
        laser_index = analog_channels.index(self.laser_channel)
        laser_mw_function[laser_index] = 'DC'
        laser_mw_params[laser_index] = {'amplitude1': laser_amp}
    # # add gate trigger for gated fast counters
    # if gate_count_chnl is not None:
    #     # Determine analogue or digital gate trigger and set parameters accordingly.
    #     if 'd_ch' in gate_count_chnl:
    #         gate_index = digital_channels.index(gate_count_chnl)
    #         laser_mw_digital[gate_index] = True
    #         delay_digital[gate_index] = True
    #     elif 'a_ch' in gate_count_chnl:
    #         gate_index = analog_channels.index(gate_count_chnl)
    #         laser_mw_function[gate_index] = 'DC'
    #         laser_mw_params[gate_index] = {'amplitude1': laser_amp}
    #         delay_function[gate_index] = 'DC'
    #         delay_params[gate_index] = {'amplitude1': laser_amp}
    # Determine analogue or digital MW channel and set parameters accordingly.
    if 'd_ch' in mw_channel:
        mw_index = digital_channels.index(mw_channel)
        laser_mw_digital[mw_index] = True
    elif 'a_ch' in mw_channel:
        mw_index = analog_channels.index(mw_channel)
        laser_mw_function[mw_index] = 'Sin'
        laser_mw_params[mw_index] = {'amplitude1': mw_amp, 'frequency1': mw_freq,
                                     'phase1': mw_phase}

    # laser_mw_function[1] = 'Sin'
    # laser_mw_params[1] = {'amplitude1': mw_amp, 'frequency1': mw_freq,
    #                              'phase1': 90.0}
    # Create laser/mw element
    laser_mw_element = PulseBlockElement(init_length_s=length, increment_s=increment,
                                         pulse_function=laser_mw_function,
                                         digital_high=laser_mw_digital, parameters=laser_mw_params,
                                         use_as_tick=use_as_tick)
    # # Create delay element
    # delay_element = PulseBlockElement(init_length_s=delay_time, increment_s=0.0,
    #                                   pulse_function=delay_function, digital_high=delay_digital,
    #                                   parameters=delay_params, use_as_tick=False)
    return laser_mw_element



def _do_channel_sanity_checks(self, **kwargs):
    """
    Does sanity checks of specified channels

    @param string kwargs: all channel descriptors to be checked (except laser channel)

    @return: error code (0: specified channels OK, -1: specified channels not OK)
    """
    # sanity checks
    error_code = 0
    for channel in kwargs:
        if kwargs[channel] is not None and kwargs[channel] != '':
            if kwargs[channel] not in self.activation_config:
                self.log.error('{0} "{1}" is not part of current activation_config!'
                               ''.format(channel, kwargs[channel]))
                error_code = -1
    return error_code

def waveform(self, block_name, waveform_name, repetitions = 0):

    # create the pulse block ensemble with params from block element
    # Create PulseBlock object
    block = PulseBlock(waveform_name, block_name)
    # save block
    self.save_block(waveform_name, block)

    # Create Block list with repetitions and sequence trigger if needed.
    # remember number_of_taus=0 also counts as first round.
    block_list = [(block, repetitions)]

    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=waveform_name, block_list=block_list, rotating_frame=True)
    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = True
    block_ensemble.laser_ignore_list = []
    block_ensemble.controlled_vals_array = np.array([])
    # save ensemble
    self.save_ensemble(waveform_name, block_ensemble)
    return block_ensemble