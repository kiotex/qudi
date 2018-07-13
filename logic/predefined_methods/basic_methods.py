# -*- coding: utf-8 -*-

"""
This file contains the Qudi Predefined Methods for sequence generator

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

def generate_laser_on(self, name='laser_on', length=3.0e-6, channel_amp=2.0):

    """ Generates Laser on.

    @param str name: Name of the PulseBlockEnsemble
    @param float length: laser duration in seconds
    @param float channel_amp: In case of analogue laser channel this value will be the laser on
                              voltage.
    @return object: the generated PulseBlockEnsemble object.
    """
    # create the laser element
    laser_element, delay_element = self._get_laser_element(length, 0.0, False, amp_V=channel_amp)

    # Create the element list
    element_list = [laser_element]
    # create the PulseBlock object.
    block = PulseBlock(name, element_list)
    # save block
    self.save_block(name, block)
    # put block in a list with repetitions
    block_list = [(block, 0)]
    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=False)
    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = False
    block_ensemble.laser_ignore_list = []
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_laser_mw_on(self, name='Laser_MW_On', laser_amp=2.0, mw_channel='a_ch1',
                         mw_freq=0.1e+9, mw_amp=0.25):
    """ General generation method for laser on and microwave on generation.

    @param string name: Name of the PulseBlockEnsemble to be generated
    @param float length: Length of the PulseBlockEnsemble in seconds
    @param float channel_amp: In case of analog laser channel this value will be the laser on voltage.
    @param string mw_channel: The pulser channel controlling the MW. If set to 'd_chX' this will be
                              interpreted as trigger for an external microwave source. If set to
                              'a_chX' the pulser (AWG) will act as microwave source.
    @param float mw_freq: MW frequency in case of analogue MW channel in Hz
    @param float mw_amp: MW amplitude in case of analogue MW channel

    @return object: the generated PulseBlockEnsemble object.
    """

    length = (1.0/mw_freq)*50

    # sanity checks for input parameters
    err_code = self._do_channel_sanity_checks(mw_channel=mw_channel)
    if err_code != 0:
        return

    laser_mw_element = self._get_mw_laser_element(length, 0.0, mw_channel, False,
                                                                 laser_amp=laser_amp, mw_amp=mw_amp,
                                                                 mw_freq=mw_freq, mw_phase=0.0)
    # Create the element list.
    element_list = [laser_mw_element]
    # create the PulseBlock object.
    block = PulseBlock(name, element_list)
    # save block
    self.save_block(name, block)
    # put block in a list with repetitions
    block_list = [(block, 0)]
    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=True)
    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = False
    block_ensemble.laser_ignore_list = []
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_idle(self, name='idle', length=3.0e-6):

    """ Generate just a simple idle ensemble.

    @param str name: Name of the PulseBlockEnsemble to be generated
    @param float length: Length of the PulseBlockEnsemble in seconds

    @return object: the generated PulseBlockEnsemble object.
    """
    # generate idle element
    idle_element = self._get_idle_element(length, 0.0, False)
    # Create the element list.
    element_list = [idle_element]
    # create the PulseBlock object.
    block = PulseBlock(name, element_list)
    # put block in a list with repetitions
    block_list = [(block, 0)]
    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=False)
    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = False
    block_ensemble.laser_ignore_list = []
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_rabi(self, name='rabi', tau_start=10.0e-9, tau_step=10.0e-9, number_of_taus=50,
                  mw_freq=100e6, mw_amp=0.25, mw_channel='a_ch1', laser_length=3.0e-6,
                  channel_amp=1.0, delay_length=0.7e-6, wait_time=1.0e-6, sync_trig_channel='',
                  gate_count_channel='d_ch2'):

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
    # get MW element
    mw_element = self._get_mw_element(tau_start, tau_step, mw_channel, True, mw_amp, mw_freq, 0.0, gate_count_channel)
    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length,
                                                           channel_amp)

    if sync_trig_channel is not None:
        # get sequence trigger element
        seqtrig_element = self._get_trigger_element(20.0e-9, 0.0, sync_trig_channel,
                                                    amp=channel_amp)
        # Create its own block out of the element
        seq_block = PulseBlock('seq_trigger', [seqtrig_element])
        # save block
        self.save_block('seq_trigger', seq_block)

    # Create element list for Rabi PulseBlock
    element_list = [mw_element, laser_element, delay_element, waiting_element]
    # Create PulseBlock object
    rabi_block = PulseBlock(name, element_list)
    # save block
    self.save_block(name, rabi_block)

    # Create Block list with repetitions and sequence trigger if needed.
    # remember number_of_taus=0 also counts as first round.

    block_list = [(rabi_block, number_of_taus-1)]
    if sync_trig_channel is not None:
        block_list.append((seq_block, 0))

    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=False)
    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = False
    block_ensemble.laser_ignore_list = []
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_pulsed_odmr(self, name='pulsed_ODMR', rabi_period=200.0e-9, mw_freq_start = 100.0e6,
                        mw_freq_incr=0.2e6, num_of_points=50, mw_amp=0.25, mw_channel='a_ch1',
                        laser_length=3.0e-6, channel_amp=1.0, delay_length=0.7e-6, wait_time=1.0e-6,
                        sync_trig_channel='', gate_count_channel=''):
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
    if sync_trig_channel is not None:
        # get sequence trigger element
        seqtrig_element = self._get_trigger_element(20.0e-9, 0.0, sync_trig_channel,
                                                    amp=channel_amp)
        # Create its own block out of the element
        seq_block = PulseBlock('seq_trigger', [seqtrig_element])
        # save block
        self.save_block('seq_trigger', seq_block)

    # Create frequency list array
    freq_array = mw_freq_start + np.arange(num_of_points) * mw_freq_incr

    # Create element list for PulsedODMR PulseBlock
    element_list = []
    for mw_freq in freq_array:
        mw_element = self._get_mw_element(rabi_period/2, 0.0, mw_channel, False, mw_amp, mw_freq,
                                          0.0, gate_count_channel)
        element_list.append(mw_element)
        element_list.append(laser_element)
        element_list.append(delay_element)
        element_list.append(waiting_element)
    # Create PulseBlock object
    pulsedodmr_block = PulseBlock(name, element_list)
    # save block
    self.save_block(name, pulsedodmr_block)

    # Create Block list with repetitions and sequence trigger if needed.
    # remember number_of_taus=0 also counts as first round.
    block_list = [(pulsedodmr_block, 0)]
    if sync_trig_channel is not None:
        block_list.append((seq_block, 0))

    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=False)
    # add metadata to invoke settings later on
    block_ensemble.controlled_vals_array = freq_array
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = False
    block_ensemble.laser_ignore_list = []
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_ramsey(self, name='ramsey', rabi_period=1.0e-6, mw_freq=2870.0e6, mw_amp=0.1,
                    tau_start=1.0e-6, tau_incr=1.0e-6, num_of_points=50, mw_channel='a_ch1',
                    laser_length=3.0e-6, channel_amp=1.0, delay_length=0.7e-6, wait_time=1.0e-6,
                    sync_trig_channel='', gate_count_channel='', alternating=True):
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
    tau_array = tau_start + np.arange(num_of_points) * tau_incr
    # calculate "true" tau start value due to finite length of pi/pihalf pulses
    real_tau_start = tau_start - rabi_period / 4

    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)

    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length,
                                                           channel_amp, gate_count_channel)
    # get pihalf element
    pihalf_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq,
                                          0.0, gate_count_channel)
    # get 3pihalf element
    pi3half_element = self._get_mw_element(3 * rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 0.0, gate_count_channel)
    # get tau element
    tau_element = self._get_idle_element(real_tau_start, tau_incr, True, gate_count_channel)

    if sync_trig_channel is not None:
        # get sequence trigger element
        seqtrig_element = self._get_trigger_element(20.0e-9, 0.0, sync_trig_channel,
                                                    amp=channel_amp)
        # Create its own block out of the element
        seq_block = PulseBlock('seq_trigger', [seqtrig_element])
        # save block
        self.save_block('seq_trigger', seq_block)

    # Create element list for alternating Ramsey PulseBlock
    element_list = []
    element_list.append(pihalf_element)
    element_list.append(tau_element)
    element_list.append(pihalf_element)
    element_list.append(laser_element)
    element_list.append(delay_element)
    element_list.append(waiting_element)

    if alternating:
        element_list.append(pihalf_element)
        element_list.append(tau_element)
        element_list.append(pi3half_element)
        element_list.append(laser_element)
        element_list.append(delay_element)
        element_list.append(waiting_element)

    # Create PulseBlock object
    ramsey_block = PulseBlock(name, element_list)
    # save block
    self.save_block(name, ramsey_block)

    # Create Block list with repetitions and sequence trigger if needed.
    # remember number_of_taus=0 also counts as first round.
    block_list = [(ramsey_block, num_of_points - 1)]
    if sync_trig_channel is not None:
        block_list.append((seq_block, 0))

    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=True)

    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = alternating
    block_ensemble.laser_ignore_list = []
    block_ensemble.controlled_vals_array = tau_array
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_Hahn_echo(self, name='hahn_echo', rabi_period=200e-9, mw_freq=100.0e6, mw_amp=0.25,
                      tau_start=300.0e-9, tau_incr=500.0e-9, num_of_points=50, mw_channel='a_ch1',
                      laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6, wait_time=1.0e-6,
                      sync_trig_channel='', gate_count_channel='d_ch2', alternating=True):

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

    # get tau array for measurement ticks
    tau_array = tau_start + np.arange(num_of_points) * tau_incr
    # calculate "true" tau start value due to finite length of pi/pihalf pulses
    real_tau_start = tau_start - 3 * rabi_period / 8

    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)

    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length,
                                                           channel_amp, gate_count_channel)
    # get pihalf element
    pihalf_element = self._get_mw_element(rabi_period / 4, 0.0, mw_channel, False, mw_amp, mw_freq,
                                          0., gate_count_channel)
    # get 3pihalf element
    pi3half_element = self._get_mw_element(3 * rabi_period / 4, 0.0, mw_channel, False, mw_amp,
                                           mw_freq, 0.0, gate_count_channel)
    # get pi element
    pi_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0, gate_count_channel)
    # get tau element
    tau_element = self._get_idle_element(real_tau_start, tau_incr, False, gate_count_channel)

    if sync_trig_channel is not None:
        # get sequence trigger element
        seqtrig_element = self._get_trigger_element(20.0e-9, 0.0, sync_trig_channel,
                                                    amp=channel_amp)
        # Create its own block out of the element
        seq_block = PulseBlock('seq_trigger', [seqtrig_element])
        # save block
        self.save_block('seq_trigger', seq_block)

    # Create element list for alternating Hahn Echo PulseBlock
    element_list = []
    element_list.append(pihalf_element)
    element_list.append(tau_element)
    element_list.append(pi_element)
    element_list.append(tau_element)
    element_list.append(pihalf_element)
    element_list.append(laser_element)
    element_list.append(delay_element)
    element_list.append(waiting_element)

    if alternating:
        element_list.append(pihalf_element)
        element_list.append(tau_element)
        element_list.append(pi_element)
        element_list.append(tau_element)
        element_list.append(pi3half_element)
        element_list.append(laser_element)
        element_list.append(delay_element)
        element_list.append(waiting_element)

    # Create PulseBlock object
    hahn_block = PulseBlock(name, element_list)
    # save block
    self.save_block(name, hahn_block)

    # Create Block list with repetitions and sequence trigger if needed.
    # remember number_of_taus=0 also counts as first round.
    block_list = [(hahn_block, num_of_points - 1)]
    if sync_trig_channel is not None:
        block_list.append((seq_block, 0))

    # create ensemble out of the block(s)
    block_ensemble = PulseBlockEnsemble(name=name, block_list=block_list, rotating_frame=True)
    # add metadata to invoke settings later on
    block_ensemble.sample_rate = self.sample_rate
    block_ensemble.activation_config = self.activation_config
    block_ensemble.amplitude_dict = self.amplitude_dict
    block_ensemble.laser_channel = self.laser_channel
    block_ensemble.alternating = alternating
    block_ensemble.laser_ignore_list = []
    block_ensemble.controlled_vals_array = tau_array
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_T1_waveform(self, name='T1', rabi_period=200e-9, mw_freq=100.0e6, mw_amp=0.25,
                      tau_start=300.0e-9, tau_incr=100e-6, num_of_points=20, mw_channel='a_ch1',
                      laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6, wait_time=1.0e-6,
                      sync_trig_channel='', gate_count_channel='d_ch2'):
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
    tau_array = tau_start + np.arange(num_of_points) * tau_incr
    # calculate "true" tau start value due to finite length of pi/pihalf pulses
    real_tau_start = tau_start - rabi_period/2

    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length,
                                                           channel_amp, gate_count_channel)
    # get pi element
    pi_element = self._get_mw_element(rabi_period / 2, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0, gate_count_channel)
    # get tau element
    tau_element = self._get_idle_element(real_tau_start, tau_incr, False, gate_count_channel)

    if sync_trig_channel is not None:
        # get sequence trigger element
        seqtrig_element = self._get_trigger_element(20.0e-9, 0.0, sync_trig_channel,
                                                    amp=channel_amp)
        # Create its own block out of the element
        seq_block = PulseBlock('seq_trigger', [seqtrig_element])
        # save block
        self.save_block('seq_trigger', seq_block)

    # Create element list for alternating Hahn Echo PulseBlock
    element_list = []
    element_list.append(pi_element)
    element_list.append(tau_element)
    element_list.append(pi_element)
    element_list.append(laser_element)
    element_list.append(delay_element)
    element_list.append(waiting_element)

    element_list.append(pi_element)
    element_list.append(tau_element)
    element_list.append(laser_element)
    element_list.append(delay_element)
    element_list.append(waiting_element)

    # Create PulseBlock object
    hahn_block = PulseBlock(name, element_list)
    # save block
    self.save_block(name, hahn_block)

    # Create Block list with repetitions and sequence trigger if needed.
    # remember number_of_taus=0 also counts as first round.
    block_list = [(hahn_block, num_of_points - 1)]
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
    block_ensemble.controlled_vals_array = tau_array
    # save ensemble
    self.save_ensemble(name, block_ensemble)
    return block_ensemble

def generate_T1_sequence(self, name='T1 sequence', rabi_period=200e-9, mw_freq=100.0e6, mw_amp=0.25,
                      tau_start=300.0e-9, tau_incr=0.5e-6, num_of_points=5, mw_channel='a_ch1',
                      laser_length=3.0e-6, channel_amp=2.0, delay_length=0.7e-6, wait_time=1.0e-6,
                      sync_trig_channel='', gate_count_channel='d_ch2'):
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
    tau_array = tau_start + np.arange(num_of_points) * tau_incr
    # create the static waveform elements

    # get waiting element
    waiting_element = self._get_idle_element(wait_time, 0.0, False, gate_count_channel)
    # get laser and delay element
    laser_element, delay_element = self._get_laser_element(laser_length, 0.0, False, delay_length,
                                                           channel_amp, gate_count_channel)

    readout = waveform(self, [laser_element, delay_element, waiting_element], 'READOUT')
    # get pi element
    pi_element = self._get_mw_element(rabi_period/2, 0.0, mw_channel, False, mw_amp, mw_freq, 0.0, gate_count_channel)
    flip = waveform(self, [pi_element], 'FLIP')
    # Create sequence
    mainsequence_list = []
    i=0

    for t in tau_array:

        length = (1.0 / mw_freq) * 51
        subsequence_list = []

        if t <= length:
            tau_element = self._get_idle_element(t - rabi_period / 2, 0.0, False, gate_count_channel)
            name1 = 'EVO1_X%02i' % i
            evo1 = waveform(self, [tau_element], name1)

            subsequence_list.append((flip, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((evo1, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((flip, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            subsequence_list.append((flip, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((evo1, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        else:

            rep = int((t - rabi_period / 2) // length)
            rest = (t - rabi_period / 2) - rep * length

            # get tau element
            tau_element1 = self._get_idle_element(length, 0.0, False, gate_count_channel)
            tau_element2 = self._get_idle_element(rest, 0.0, False, gate_count_channel)

            name1 = 'EVO1_X%02i' % i
            evo1 = waveform(self, [tau_element1], name1)
            name2 = 'EVO2_X%02i' % i
            evo2 = waveform(self, [tau_element2], name2)

            subsequence_list.append((flip, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((evo1, {'repetitions': rep, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((evo2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((flip, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

            # # get tau element
            # tau_element2 = self._get_idle_element(t - rabi_period/4, 0.0, False, gate_count_channel)
            # name2 = 'EVO2_X%04i' % i
            # evo2 = waveform(self, [tau_element2], name2)

            subsequence_list.append((flip, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((evo1, {'repetitions': rep, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((evo2, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))
            subsequence_list.append((readout, {'repetitions': 1, 'trigger_wait': 0, 'go_to': 0, 'event_jump_to': 0}))

        i=i+1
        mainsequence_list.extend(subsequence_list)

    sequence = PulseSequence(name = name, ensemble_param_list = mainsequence_list, rotating_frame=True)

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
