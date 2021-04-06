# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 11:44:52 2015

@author: Ali.Eftekhari
"""
import visa
from core.module import Base, ConfigOption
import abc
from core.util.interfaces import InterfaceMetaclass

class MagnetController(metaclass=InterfaceMetaclass):

    _modclass = 'MagnetController'
    _modtype = 'interface'

    @abc.abstractmethod
    def send(self, command):

        pass

    @abc.abstractmethod
    def write_read(self, command):
        pass

    @abc.abstractmethod
    def read(self):
        pass

    @abc.abstractmethod
    def get_acceleration(self,axis):
        pass

    @abc.abstractmethod
    def set_acceleration(self,axis,value):
        pass

    @abc.abstractmethod
    def get_backlash(self,axis):
        pass

    @abc.abstractmethod
    def set_backlash(self,axis,value):
        pass

    @abc.abstractmethod
    def get_following_error(self,axis):
        pass

    @abc.abstractmethod
    def set_following_error(self,axis,value):
        pass

    @abc.abstractmethod
    def get_stage_modelnumber(self, axis):
        pass

    @abc.abstractmethod
    def set_stage_modelnumber(self,axis,value):
        pass

    @abc.abstractmethod
    def get_derivative_gain(self, axis):
        pass

    @abc.abstractmethod
    def set_derivative_gain(self, axis,value):
        pass

    @abc.abstractmethod
    def get_integral_gain(self, axis):
        pass

    @abc.abstractmethod
    def set_integral_gain(self, axis,value):
        pass

    @abc.abstractmethod
    def get_proportional_gain(self, axis):
        pass

    @abc.abstractmethod
    def set_proportional_gain(self, axis,value):
        pass

    @abc.abstractmethod
    def move_absolute(self, axis,value):
        pass

    @abc.abstractmethod
    def move_relative(self, axis,value):
        pass

    @abc.abstractmethod
    def get_motor_currentlimit(self, axis):
        pass

    @abc.abstractmethod
    def set_motor_currentlimit(self, axis,value):
        pass

    @abc.abstractmethod
    def set_controller_addrees(self, axis,value):
        pass

    @abc.abstractmethod
    def get_controller_addrees(self, axis):
        pass

    @abc.abstractmethod
    def reset_controller(self, axis):
        pass

    @abc.abstractmethod
    def stop_motion(self, axis):
        pass

    @abc.abstractmethod
    def get_negative_softwarelimit(self, axis):
        pass

    @abc.abstractmethod
    def set_negative_softwarelimit(self, axis,value):
        pass

    @abc.abstractmethod
    def get_positive_softwarelimit(self, axis):
        pass

    @abc.abstractmethod
    def set_positive_softwarelimit(self, axis,value):
        pass

    @abc.abstractmethod
    def get_encodercount(self, axis):
        pass

    @abc.abstractmethod
    def set_encodercount(self, axis,value):
        pass

    @abc.abstractmethod
    def get_error_message(self, axis):
        pass

    @abc.abstractmethod
    def get_error_code(self, axis):
        pass

    @abc.abstractmethod
    def get_current_position(self, axis):
        pass

    @abc.abstractmethod
    def get_positioner_error(self, axis):
        pass

    @abc.abstractmethod
    def get_velocity(self, axis):
        pass

    @abc.abstractmethod
    def set_velocity(self, axis,value):
        pass

    @abc.abstractmethod
    def get_firmware_version(self, axis):
        pass

    @abc.abstractmethod
    def save_settings(self):
        pass

    @abc.abstractmethod
    def get_hysteresis(self,axis):
        pass

    @abc.abstractmethod
    def set_hysteresis(self,axis,value):
        pass

    @abc.abstractmethod
    def get_driver_voltage(self,axis):
        pass

    @abc.abstractmethod
    def set_driver_voltage(self,axis,value):
        pass

    @abc.abstractmethod
    def get_lowpass_filter(self,axis):
        pass

    @abc.abstractmethod
    def set_lowpass_filter(self,axis,value):
        pass

    @abc.abstractmethod
    def get_friction_compensation(self,axis):
        pass
        
    def set_friction_compensation(self,axis,value):
        pass

    @abc.abstractmethod
    def get_home_search_type(self,axis):
        pass

    @abc.abstractmethod
    def set_home_search_type(self,axis,value):
        pass

    @abc.abstractmethod
    def get_jerktime(self,axis):
        pass

    @abc.abstractmethod
    def set_jerktime(self,axis,value):
        pass

    @abc.abstractmethod
    def get_enable_disable_state(self,axis):
        pass

    @abc.abstractmethod
    def set_enable_disable_state(self,axis,value):
        pass

    @abc.abstractmethod
    def home(self,axis):
        pass

    @abc.abstractmethod
    def get_homeserach_timeout(self,axis):
        pass

    @abc.abstractmethod
    def set_homeserach_timeout(self,axis,value):
        pass

    @abc.abstractmethod
    def enter_configuration(self,axis):
        pass

    @abc.abstractmethod
    def leave_configuration(self,axis):
        pass

    @abc.abstractmethod
    def move_absolute_axisnumber(self,axis,value):
        pass

    @abc.abstractmethod
    def get_motiontime_relativemove(self, axis,value):
        pass

    @abc.abstractmethod
    def get_controller_loopstate(self, axis):
        pass

    @abc.abstractmethod
    def close_controllerloop(self, axis):
        pass

    @abc.abstractmethod
    def open_controllerloop(self, axis):
        pass

    @abc.abstractmethod
    def configure_simultaneous_startmove(self,number_of_axis):
        pass

    @abc.abstractmethod
    def get_setpoint_position(self, axis):
        pass

    @abc.abstractmethod
    def enter_trackingmode(self, axis):
        pass

    @abc.abstractmethod
    def leave_trackingmode(self, axis):
        pass

    @abc.abstractmethod
    def get_configuration_parameters(self, axis):
        pass

    @abc.abstractmethod
    def get_homeserach_velocity(self, axis):
        pass

    @abc.abstractmethod
    def set_homeserach_velocity(self, axis,value):
        pass

    @abc.abstractmethod
    def get_base_velocity(self, axis):
        pass

    @abc.abstractmethod
    def set_base_velocity(self, axis,value):
        pass

    @abc.abstractmethod
    def get_microstep(self, axis):
        pass

    @abc.abstractmethod
    def set_microstep(self, axis,value):
        pass

    @abc.abstractmethod
    def leave_jogging(self, axis):
        pass

    @abc.abstractmethod
    def leave_keypad(self, axis):
        pass

    @abc.abstractmethod
    def enter_keypad(self, axis):
        pass

    @abc.abstractmethod
    def get_TTL_output(self, axis):
        pass

    @abc.abstractmethod
    def set_TTL_output(self, axis,value):
        pass

    @abc.abstractmethod
    def get_ESP_configuration(self, axis):
        pass

    @abc.abstractmethod
    def set_ESP_configuration(self, axis,value):
        pass

    @abc.abstractmethod
    def get_velocity_feedforward(self, axis):
        pass

    @abc.abstractmethod
    def set_velocity_feedforward(self, axis,value):
        pass
        
 