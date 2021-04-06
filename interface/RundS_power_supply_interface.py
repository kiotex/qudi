import abc
from core.util.interfaces import InterfaceMetaclass

class PowerSupply(metaclass=InterfaceMetaclass):

    _modclass = 'PowerSupply'
    _modtype = 'interface'

    @abc.abstractmethod
    def _get_limit_current(self):
        pass

    @abc.abstractmethod
    def _set_limit_current(self, val):
        pass

    @abc.abstractmethod
    def _get_limit_voltage(self):
        pass

    @abc.abstractmethod
    def _set_limit_voltage(self, val):
        pass

    @abc.abstractmethod
    def _get_voltage(self):
        pass

    @abc.abstractmethod
    def _set_voltage(self, val):
        pass

    @abc.abstractmethod
    def _get_current(self):
        pass

    @abc.abstractmethod
    def _set_current(self, val):
        pass

    @abc.abstractmethod
    def _get_capacitor(self):
        pass

    @abc.abstractmethod
    def _set_capacitor(self, val):
        pass

    @abc.abstractmethod
    def get_error(self):
        pass

    @abc.abstractmethod
    def reset_error(self):
        pass

    @abc.abstractmethod
    def get_inv(self):
        pass

    @abc.abstractmethod
    def set_inv(self, val):
        pass