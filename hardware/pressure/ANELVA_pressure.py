# -*- coding: utf-8 -*-
"""
ANELVA M-601GC制御用コード

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
from core.configoption import ConfigOption
from interface.process_interface import ProcessInterface
from interface.process_control_interface import ProcessControlInterface

import serial


class M601GC(Base, ProcessInterface):
    """ Methods to control ANELVA M-601GC.
    https://dia-pe-titech.esa.io/posts/251

    Example config for copy-paste:

    process_dummy:
        module.Class: 'ANELVA_pressure.M-601GC'
        port: 'COM5'
        baudrate: 9600
        timeout: 1
    """

    _port = ConfigOption('port')
    _baudrate = ConfigOption('baudrate', 9600, missing='warn')
    _timeout = ConfigOption('timeout', 1, missing='warn')

    CMD_RETRY_NUM = 10
    CMD_ZERO_NUM = 100

    STX = b'$'
    ETX = b'\r'

    def on_activate(self):
        """ Activate module.
        """
        self._serial_connection = serial.Serial(
            port=self._port,
            baudrate=self._baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self._timeout)

        self._openflag = self._serial_connection.is_open
        if not(self._openflag):
            self._serial_connection.open()

        self.gaugetype = self.get_gaugetype()
        self.log.info('Gauge type: {0}'.format(self.gaugetype))

        self.start_reading_process_value(refresh_rate=1)

    def on_deactivate(self):
        """ Deactivate module.
        """
        self.get_gaugetype()
        self._serial_connection.close()

    def get_gaugetype(self):
        return self._send_cmd(b'$TID\r').strip('$ \r')

    def get_name(self):
        return self.gaugetype

    def get_process_unit(self, channel=None):
        """ Process unit, here Pa.

            @return float: process unit
        """
        return 'Pa', 'pascal'

    def get_process_value(self, channel=None):
        """ Process value, here temperature.

            @return float: process value
        """
        #res = self._send_cmd(b'$PRD\r')
        res = self._read_data().decode()
        while self._serial_connection.in_waiting > 0:
            res = self._read_data().decode()

        # Example: res = '$0,-0.0002E+05\r'
        errornum = int(res[1])

        if errornum != 0:
            errorlist = [
                'オーバーレンジ',
                'アンダーレンジ',
                'コントローラエラー(Err03, Err04)',
                '未使用',
                'ゲージ未接続状態',
                'Id抵抗エラー(ErrId)',
                '接続ゲージエラー(ErrHi, ErrLo, Err06, Err07)']
            self.log.critical('Error: {0}'.format(errorlist[errornum - 1]))
        return float(res[3:])

    def start_reading_process_value(self, refresh_rate=0.1):
        if refresh_rate >= 60:
            freqtype = b'2'  # interval is 60 sec
        elif refresh_rate >= 1:
            freqtype = b'1'  # interval is 1 sec
        else:
            freqtype = b'0'  # interval is 0.1 sec

        self._send_cmd(b'$CON,' + freqtype + b'\r')

    def _send_cmd(self, cmd):
        """ Send command
        """
        if self._serial_connection.out_waiting > 0:
            self._serial_connection.reset_output_buffer()

        if self._serial_connection.in_waiting > 0:
            self._serial_connection.reset_input_buffer()

        self._serial_connection.write(cmd)
        res = self._read_data()
        if isinstance(res, bool):
            return res
        else:
            return res.decode()

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
                    self.log.error(
                        self.__class__.__name__ +
                        '> Communication Error: This hardware might be off!')
                    return False
            elif res == self.STX:
                in_resiving_data = True
                data = res
            elif in_resiving_data:
                if res == self.ETX:
                    in_resiving_data = False
                    in_reading = False
                data += res

        return data
