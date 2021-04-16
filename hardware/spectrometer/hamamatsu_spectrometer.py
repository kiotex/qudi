# -*- coding: utf-8 -*-
"""
This module contains Hamamatsu spectrometer.

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
from interface.spectrometer_interface import SpectrometerInterface

import numpy as np

import os
import ctypes

DLL = ctypes.windll.LoadLibrary(
    r'C:\Program Files\HamamatsuMinispectrometer\DeveloperTools\ForVisualC++\SampleApl\DLL\specu1a.dll')


class Parameters(ctypes.Structure):
    _fields_ = [('IntegrationTime', ctypes.c_int),
                ('Gain', ctypes.c_byte),
                ('TriggerEdge', ctypes.c_byte),
                ('TriggerMode', ctypes.c_byte),
                ('Reserved', ctypes.c_byte), ]


class UnitInformation(ctypes.Structure):
    _fields_ = [('UnitID', ctypes.c_ubyte * 8),
                ('SensorName', ctypes.c_ubyte * 16),
                ('SerialNumber', ctypes.c_ubyte * 8),
                ('Reserved', ctypes.c_ubyte * 8),
                ('WaveLengthUpper', ctypes.c_ushort),
                ('WaveLengthLower', ctypes.c_ushort), ]


def ctypesArrayToString(arr):
    # return ''.join(chr(i) for i in arr)
    return ''.join(list(map(chr, arr)))


class HamamatsuSpectrometer(Base, SpectrometerInterface):
    """ Hamamatsu spectrometer module.

    Example config for copy-paste:

    C10083CAH:
        module.Class: 'spectrometer.hamamatsu_spectrometer.HamamatsuSpectrometer'
        productID: 0x2909
    """

    _productID = ConfigOption('productID', missing='warn')

    _param = Parameters()
    _unitInfo = UnitInformation()

    def on_activate(self):
        """ Activate module.
        """
        self._openDevice()
        self._getParameters()
        self._getUnitInformation()
        self._pixelSize = 128 * (1 << (self._unitInfo.UnitID[1] - 48))
        self._getCalibrationValue()

    def on_deactivate(self):
        """ Deactivate module.
        """
        self._closeDevice()

    def recordSpectrum(self):
        """ Record a dummy spectrum.

            @return ndarray:
                1024-value ndarray containing wavelength and intensity of simulated spectrum
        """
        return np.stack([self._wavelength, self._getSensorData()])

    def saveSpectrum(self, path, postfix=''):
        """ Dummy save function.

            @param str path: path of saved spectrum
            @param str postfix: postfix of saved spectrum file
        """
        #timestr = strftime("%Y%m%d-%H%M-%S_", localtime())
        #print( 'Dummy would save to: ' + str(path) + timestr + str(postfix) + ".spe" )
        pass

    def getExposure(self):
        """ Get exposure time.

            @return float: exposure time
        """
        return self._param.IntegrationTime

    def setExposure(self, exposureTime):
        """ Set exposure time.

            @param float exposureTime: exposure time
        """
        self._param.IntegrationTime = exposureTime
        self._setParameters()

    # =================== DLL Wrapper ========================

    def _openDevice(self):
        self.deviceHandle = DLL.USB_OpenDevice(self._productID)
        self.pipeHandle = DLL.USB_OpenPipe(self._deviceHandle)
        return 0

    def _closeDevice(self):
        DLL.USB_ClosePipe(self._pipeHandle)
        DLL.USB_CloseDevice(self._deviceHandle)
        return 0

    def _getParameters(self):
        DLL.USB_GetParameter(self._deviceHandle, ctypes.byref(self._param))

    def _setParameters(self):
        DLL.USB_SetParameter(self._deviceHandle, ctypes.byref(self._param))

    def _getUnitInformation(self):
        DLL.USB_ReadUnitInformation(
            self._deviceHandle, ctypes.byref(
                self._unitInfo))

    def _setUnitInformation(self):
        pass

    def _getCalibrationValue(self):
        calibrationValue = (ctypes.c_double * 6)()
        DLL.USB_ReadCalibrationValue(
            self._deviceHandle,
            ctypes.byref(calibrationValue))
        self._calibrationValue = np.ctypeslib.as_array(calibrationValue)
        self._wavelength = np.polyval(self._calibrationValue[::-1], range(
            1, 1 + self._pixelSize)) * 1e-9  # Send to logic in SI units (m)

    def _setCalibrationValue(self):
        pass

    def _getSensorData(self):
        # get spectrum
        specdata = (ctypes.c_ushort * self._pixelSize)()
        DLL.USB_GetSensorData(
            self._deviceHandle,
            self._pipeHandle,
            self._pixelSize,
            ctypes.byref(specdata))
        return np.ctypeslib.as_array(specdata)

    def _getSensorDataT(self):
        # get spectrum with trigger
        pass
