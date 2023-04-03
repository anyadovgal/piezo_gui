# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 15:49:03 2023

This is the KPZ101 Device Class, to be used in conjunction with the GUI for
Piezo Controller control, however it may be used by itself for KPZ101 control
in Python software - Simply comment out the catchNotEnoughDevices() method.

All information is found from the Thorlabs Motion Control Dot Net API
reference information.

Original program is built off of the KPZ101 example from
https://github.com/Thorlabs/Motion_Control_Examples.

@author: Anya
"""
import os
import time
import sys
import clr

clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.DeviceManagerCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\Thorlabs.MotionControl.GenericMotorCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.KCube.PiezoCLI.dll")
clr.AddReference("C:\\Program Files\\Thorlabs\\Kinesis\\ThorLabs.MotionControl.GenericPiezoCLI.dll")
from Thorlabs.MotionControl.DeviceManagerCLI import *
from Thorlabs.MotionControl.GenericMotorCLI import *
from Thorlabs.MotionControl.KCube.PiezoCLI import *
from Thorlabs.MotionControl.GenericPiezoCLI import Piezo
import Thorlabs.MotionControl.GenericPiezoCLI.Settings as Settings
from System import Decimal  # necessary for real world units

from Exceptions import *

class KPZ101:  
    """
    A class used to represent a Thorlabs KPZ101 device.
    
    All methods and functions are implemented separately inside class
    in order to avoid accessing the device directly from the top-level.
    
    Attributes
    ----------
    device : KCubePiezo Object
        The KPZ101 device associated with a given serial number
        with which it is initialized
    max_voltage : Decimal
        The maximum voltage that the device may reach
    cvoltage : Decimal
        The current voltage of the KPZ101 device
    jogsteps : ControlSettings::JogStepsStruct
        The current jog step settings, the focus of the code (voltage jog step)
        is accessible via jogsteps.VoltageStepSize
    serial_no : String
        The serial number with which the KPZ101 was initialized
        
    Methods
    --------
    getVoltage()
    getVoltageFloat(int rounding)
        Returns the current device voltage as a float, rounded to rounding digits
    getMaxVoltage()
    getJogSteps()
    update()
        Updates the cvoltage, mainly to reduce redundancy
    setZero()
        Sets the zero for the KPZ101 device
    setVoltage(Decimal voltage)
        Sets the current voltage to the new 'voltage',
        0 < voltage < max_voltage
        --> Note-to-self: voltage is changed almost immediately.
    setJogSteps(Decimal new_step)
        Sets the voltage jog step to new_step
        0 < new_step < 10
    jogVoltage(Boolean boolean)
        Jogs the KPZ101 voltage by jogsteps.VoltageStepSize
        If boolean == True, voltage increases.
        If boolean == False, voltage decreases.
    disconnect()
        Stops the device polling and disconnects it from the computer
    connect()
        Re-connects the device to the computer and re-starts polling
    disable()
        If device.IsConnected == True, disables the device so that the voltage
        is no longer being output
    enable()
        If device.IsConnected == True, re-enables the device so that the
        voltage may be output again.        
        ================================================================
        NOTE: Re-enabling a device keeps the memory of the previous voltage
            that was sent to it. So, if you jog the device immediately after
            re-enabling, it will make the output voltage the last voltage
            before disabling, plus the jog step.
        EX. voltage = 0.6V, jog step = 0.1
            Disable, Re-enable the device
            Current voltage is ~ 0V.
            Jog the device up : new voltage = 0.7V (Not 0.1V!)
        ================================================================
    stop()
        Disables, stops polling, and disconnects the device completely.
    """
    
    def __init__(self, serial_no):
        """
        Parameters
        ----------
        serial_no : str
            The serial number for the requested KPZ101 device

        Raises
        ------
        Exception
            If the device is not connected and/or registered by the computer,
            raise exception

        Returns
        -------
        None.

        """
        
        self.serial_no = serial_no
        
        # Building Devices
        DeviceManagerCLI.BuildDeviceList()
        self.catchNotEnoughDevices()
        self.catchMisMatchedSerial()
        
        # Check Device is being registered by computer
        if DeviceManagerCLI.GetDeviceListSize() < 1:
            raise Exception('No Device Available')
            
        # Created KCubePiezo device
        self.device = KCubePiezo.CreateKCubePiezo(serial_no)
        
        self.initialConnect()
        
        print('Initialized', serial_no)
        
        #======================================================
        self.max_voltage = self.device.GetMaxOutputVoltage()
        self.jogsteps = self.device.GetJogSteps()
        self.cvoltage = self.device.GetOutputVoltage()
        
    def catchNotEnoughDevices(self):
        i = DeviceManagerCLI.GetDeviceListSize()
        if i <= 1:
            raise DeviceCountError(i)
        
    def catchMisMatchedSerial(self):
        if not DeviceManagerCLI.IsDeviceConnected(self.serial_no):
            connected = [DeviceManagerCLI.GetDeviceList()[0], DeviceManagerCLI.GetDeviceList[1]]
            raise MisMatchSerialError(self.serial_no, connected)
        
    def getSerial(self):
        deviceInfo = self.device.GetDeviceInfo()
        return str(deviceInfo.SerialNumber)
        
    def getVoltage(self):
        return self.cvoltage
    
    def getVoltageFloat(self, rounding):
        return round(float(self.device.GetOutputVoltage().ToString()), rounding)
    
    def getMaxVoltage(self):
        return self.device.GetMaxOutputVoltage()
        
    def getJogSteps(self):
        return self.jogsteps.VoltageStepSize
    
    def isConnected(self):
        return self.device.IsConnected
    
    def initialConnect(self):
        # TODO: Simplify this method with self.connect()
        if not self.device.IsConnected:
            self.device.Connect(self.serial_no)
            assert self.device.IsConnected is True
            
        self.device.StartPolling(250)
        time.sleep(0.5)
        self.device.EnableDevice()
        time.sleep(0.25)
        
        if not self.device.IsSettingsInitialized():
            self.device.WaitForSettingsInitialized(10000)  # 10 second timeout
            assert self.device.IsSettingsInitialized() is True
    
    def update(self):
        """
        Updates the current object variable to the real-time current
        output voltage of the device.

        Returns
        -------
        None.

        """
        self.cvoltage = self.device.GetOutputVoltage()
        
    def setZero(self):
        """
        Sets the output voltage of the device to zero

        Returns
        -------
        None.

        """
        self.device.SetZero()
        
    def setVoltage(self, voltage):
        """
        Given 0 <= voltage <= max_voltage, update the output voltage of the
        KPZ101 device to 'voltage'

        Parameters
        ----------
        voltage : Decimal
            The user-input voltage to be set as the new output voltage

        Returns
        -------
        None.

        """
        if voltage >= Decimal(0) and voltage <= self.max_voltage:
            self.device.SetOutputVoltage(voltage)
            time.sleep(1)
        
    def setJogSteps(self, new_step):
        """
        Given 0 <= new_step <= 10V, update KPZ101 VOLTAGE jog step to new_step

        Parameters
        ----------
        new_step : Decimal
            The user-input VOLTAGE jog step to be set as the new current
            VOLTAGE jog step for the device

        Returns
        -------
        None.

        """
        if new_step >= Decimal(0) and new_step <= Decimal(10):
            self.jogsteps.VoltageStepSize = new_step
            self.device.SetJogSteps(self.jogsteps)
            time.sleep(0.25)
        
    def jogVoltage(self, boolean):
        """
        Given Boolean boolean, jog the voltage by the voltage jog step.
          If boolean == True: Increase voltage
          If boolean == False: Decrease voltage

        Parameters
        ----------
        boolean : Boolean
            The boolean representation of jog 'direction'

        Returns
        -------
        None.

        """
        Increase = Settings.ControlSettings.PiezoJogDirection.Increase
        Decrease = Settings.ControlSettings.PiezoJogDirection.Decrease
        if self.cvoltage >= Decimal(0) and self.cvoltage <= self.max_voltage:
            if boolean:
                self.device.Jog(Increase)
                
            else:
                self.device.Jog(Decrease)
                
    def disconnect(self):
        """
        Disconnect (but do not disable) the KPZ101 Device

        Returns
        -------
        None.

        """
        if self.device.IsConnected:
            self.device.StopPolling()
            time.sleep(1)
            self.device.Disconnect(False)
        
    def connect(self):        
        """
        If the device is not connected, re-connect the device and ensure
        that it is enabled and initialized.

        Returns
        -------
        None.

        """
        if not self.device.IsConnected:
            self.device.ConnectDevice(self.serial_no)
            assert self.device.IsConnected is True
            
        self.device.StartPolling(250)
        time.sleep(0.5)
        self.device.EnableDevice()
        time.sleep(0.25)
        
        if not self.device.IsSettingsInitialized():
            self.device.WaitForSettingsInitialized(10000)  # 10 second timeout
            assert self.device.IsSettingsInitialized() is True
        
    def disable(self):
        """
        Disable the device output

        Returns
        -------
        None.

        """
        self.device.DisableDevice()
        time.sleep(0.25)
        
    def enable(self):
        """
        Re-enable the device output, will start/stay at 0V.
        Read NOTE in method description at class initialization, above.

        Returns
        -------
        None.

        """
        self.device.EnableDevice()
        time.sleep(0.25)
        
    def stop(self):
        """
        Completely disconnect and disable the KPZ101 Device from the software

        Returns
        -------
        None.

        """
        self.device.DisableDevice()
        self.device.StopPolling()
        time.sleep(1)
        self.device.Disconnect(False)