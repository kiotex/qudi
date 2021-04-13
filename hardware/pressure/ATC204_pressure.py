# -*- coding: utf-8 -*-
"""
Arios ATC-204(東邦電子 TTM-204)制御用コード

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

from core.module import Base
from core.connector import Connector
from core.configoption import ConfigOption
from interface.process_interface import ProcessInterface
from interface.process_control_interface import ProcessControlInterface

import serial
import time

class ATC204(Base, ProcessInterface, ProcessControlInterface):
    """ Methods to control Arios ATC-204(東邦電子 TTM-204).
    https://dia-pe-titech.esa.io/posts/158

    Example config for copy-paste:

    APC:
        module.Class: 'ATC204_pressure.ATC204'
        port: 'COM4'
        baudrate: 9600
        timeout: 100

        limit_min: 0    # Pa
        limit_max: 40e3 # Pa
    """


    _port = ConfigOption('port')
    _baudrate = ConfigOption('baudrate', 9600, missing='warn')
    _timeout = ConfigOption('timeout', 10, missing='warn')

    _limit_min = ConfigOption('limit_min', 0, missing='warn')
    _limit_max = ConfigOption('limit_max', 40e3, missing='warn')

    CMD_RETRY_NUM = 10
    CMD_ZERO_NUM = 10

    STX = b'\x02'
    ETX = b'\x03'

    def on_activate(self):
        """ Activate module.
        """
        self._serial_connection = serial.Serial(
            port=self._port,
            baudrate=self._baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=self._timeout)

        self._openflag = self._serial_connection.is_open
        if not(self._openflag):
            self._serial_connection.open()

        # なぜか初期値が0.2になってしまうのでリセット
        if self.get_control_value() == .2e3:
            self.set_control_value( 0.0 )

    def on_deactivate(self):
        """ Deactivate module.
        """
        if not(self._openflag):
           self._serial_connection.close()


    def get_process_unit(self):
        """ Process unit, here Pa.

            @return float: process unit
        """
        return 'Pa', 'pascal'

    def get_control_unit(self):
        """ Get unit of control value.

            @return tuple(str): short and text unit of control value
        """
        return 'Pa', 'pascal'

    def get_control_limit(self):
        """ Get minimum and maximum of control value.

            @return tuple(float, float): minimum and maximum of control value
        """
        return self._limit_min, self._limit_max


    def get_minimal_step(self):
        return 100.0




    def get_process_value(self):
        """ Process value, here temperature.

            @return float: process value
        """
        return self._send_cmd('01RPV1')*1e3


    def get_control_value(self):
        """ Get current control value, here heating power

            @return float: current control value
        """
        return self._send_cmd('01RSV1')*1e3


    def set_control_value(self, value):
        """ Set control value, here heating power.

            @param flaot value: control value
        """

        set_value = round( value / 1e3 * 10)
        cmd = '01WSV1' + str(set_value).zfill(5)
        #'01WSV1' + '{:0=5}'.format( set_value ) でも同じ結果になる

        return self._send_cmd(cmd)*1e3
        #print(cmd)
        #return True




    def _send_cmd(self, cmd):
        """ Send command
        """

        cmd = self.STX + cmd.encode() + self.ETX

        bcc=0
        for data in cmd:
            bcc = bcc ^ data

        final_cmd = cmd + bytes([bcc])


        for i in range(self.CMD_RETRY_NUM):
            #if self._serial_connection.out_waiting > 0:
            #    self._serial_connection.reset_output_buffer()

            self._serial_connection.write(final_cmd)
            res = self._read_data()

            if res == False:
                return False
            elif res == b'\x0201\x06\x03\x06':
                return True
            else:
                try:
                    return float( res[7:12].decode() )/10
                except ValueError:
                    # clear receive buffer
                    self._serial_connection.reset_input_buffer()
                    self.log.warning('clear receive buffer')

        self.log.critical('cmd res error:', res)
        return False


    def _read_data(self):
        in_reading = True
        in_resiving_data = False

        _num_of_zero = 0
        data = b''

        while in_reading:
            res = self._serial_connection.read(1)

            if res == b'\x00' or res == b'':
                _num_of_zero += 1
                if _num_of_zero >= self.CMD_ZERO_NUM:
                    self.log.error( self.__class__.__name__ + '> Communication Error: This hardware might be off!' )
                    return False
            elif res == self.STX:
                in_resiving_data = True
                data = res
            elif in_resiving_data:
                if res == self.ETX:
                    in_resiving_data = False
                    in_reading = False
                data += res


        #BCC
        res = self._serial_connection.read(1)
        data += res

        return data


