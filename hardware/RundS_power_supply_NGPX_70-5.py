import visa
from core.module import Base, ConfigOption
from interface.RundS_power_supply_interface import PowerSupply


class Power_supply(Base, PowerSupply):
    _modclass = 'Power_supply'
    _modtype = 'hardware'
    _gpib_address = ConfigOption('gpib_address', missing='error')
    _gpib_timeout = ConfigOption('gpib_timeout', 10, missing='warn')

    def on_activate(self):
        self._gpib_timeout = self._gpib_timeout * 1000
        # trying to load the visa connection to the module
        self.rm = visa.ResourceManager()
        try:
            self._gpib_connection = self.rm.open_resource(self._gpib_address,
                                                          timeout=self._gpib_timeout)
        except:
            self.log.error('This is MWSMIQ: could not connect to GPIB address >>{}<<.'
                           ''.format(self._gpib_address))
            raise

    def on_deactivate(self):
        pass

    def _get_limit_current(self):
        return float(self._gpib_connection.query('IMAX?'))

    def _set_limit_current(self, val):
        self._gpib_connection.write('IMAX %.4f' % float(val))

    def _get_limit_voltage(self):
        return float(self._gpib_connection.query('VMAX?'))

    def _set_limit_voltage(self, val):
        self._gpib_connection.write('VMAX %.4f' % float(val))

    def _get_voltage(self):
        return float(self._gpib_connection.query('VOUT?')) * (-1) ** int(self._gpib_connection.query('INV?'))

    def _set_voltage(self, val):
        self._gpib_connection.write('VSET %.4f' % float(val))

    def _get_current(self):
        return float(self._gpib_connection.query('IOUT?')) * (-1) ** int(self._gpib_connection.query('INV?'))

    def _set_current(self, val):
        inverted = bool(int(self._gpib_connection.query('INV?')))
        if val == 0:  # shut down coils
            self._gpib_connection.write('ISET 0')
            self._gpib_connection.write('OUT 0')
            self._gpib_connection.write('INV 0')
        else:
            # sign = val>0
            sign = val < 0
            if sign != inverted:  # need to shut down and set invert first, was ==
                self._gpib_connection.write('ISET 0')
                self._gpib_connection.write('OUT 0')
                self._gpib_connection.write('INV %i' % sign)
            self._gpib_connection.write('OUT 1')  # turn on (if it was not already turned on)
            self._gpib_connection.write('ISET %.4f' % abs(float(val)))
            #        time.sleep(0.5) # wait a little until current is stabilized

    def _get_capacitor(self):
        return bool(self._gpib_connection.query('CAP?'))

    def _set_capacitor(self, val):
        if val == 0:
            self._gpib_connection.write('CAP 0')
        elif val == 1:
            self._gpib_connection.write('CAP 1')

    def get_error(self):
        return bool(self._gpib_connection.query('ACK?'))

    def reset_error(self):
        self._gpib_connection.write('ACK')

    def get_inv(self):
        return bool(self._gpib_connection.query('INV?'))

    def set_inv(self, val):
        if val == 1:
            self._gpib_connection.write('INV 1')
        elif val == 0:
            self._gpib_connection.write('INV 0')