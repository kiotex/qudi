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
            
        self.gaugetype = self._send_cmd(b'$TID\r').strip('$ \r')
        self.log.info('Gauge type: {0}'.format( self.gaugetype ))


    def on_deactivate(self):
        """ Deactivate module.
        """
        self._serial_connection.close()




    def get_name(self):
        return self.gaugetype

    def get_process_unit(self):
        """ Process unit, here Pa.

            @return float: process unit
        """
        return 'Pa', 'pascal'




    def get_process_value(self):
        """ Process value, here temperature.

            @return float: process value
        """
        res = self._send_cmd(b'$PRD\r')
        # Example: res = '$0,-0.0002E+05\r'
        errornum = int(res[1])
        
        if errornum != 0:
            errorlist= ['オーバーレンジ', 'アンダーレンジ', 'コントローラエラー(Err03, Err04)', '未使用', 'ゲージ未接続状態', 'Id抵抗エラー(ErrId)', '接続ゲージエラー(ErrHi, ErrLo, Err06, Err07)']
            self.log.warning('Error: {0}'.format( errorlist[errornum-1] ))
        return float(res[3:])


    def _send_cmd(self, cmd):
        """ Send command
        """
        
        for i in range(self.CMD_RETRY_NUM):
            #if self._serial_connection.out_waiting > 0:
            #    self._serial_connection.reset_output_buffer()
            
            self._serial_connection.write(cmd)
            res = self._serial_connection.read(15).decode()
            
            if res[-1] == '\r':
                return res
            else:
                self._serial_connection.reset_input_buffer()
                self.log.warning('clear receive buffer')

        self.log.warning('cmd res error:', res)
        return False


