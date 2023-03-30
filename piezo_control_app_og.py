# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 11:17:57 2023

@author: Anya
"""

# TODO: Check whether it is worth accounting for the 0.05,6V voltage difference

#%% Package imports for software operation
# Need to check that 'ctypes' package is also installed to environment
# If not, either add via Anaconda package installation system, or run
#    pip install ctypes
# NI-Visa and Thorlabs Kinesis should also be installed and up-to-date

import os
import time
import sys
import clr
import json

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

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QTimer

#%%
# Write and close the j-son file for saving the serial numbers of the piezo
#   controllers.

# dictionary = {'serialX' : '29251927',
#               'serialY' : '29251900'}

# with open("saved_serial_numbers.json", "w") as outfile:
#     json.dump(dictionary, outfile)

#%%
# Set-up the serial numbers for the two KPZ101s
with open('saved_serial_numbers.json', 'r') as openfile:
 
    # Reading from json file
    json_object = json.load(openfile)
 
serial_no_x = json_object['serialX']
serial_no_y = json_object['serialY']

# serial_no_x = '29251927'
# serial_no_y = '29251900' 

try:
    assert (serial_no_x.isnumeric() & (len(serial_no_x) == 8))
    assert (serial_no_y.isnumeric() & (len(serial_no_y) == 8))
except:
    print('Need to set-up both KPZ101 serial numbers')

#%%

def main():
    try:
        startGUI()
    except Exception as e:
        print(e)

class KPZ101:  
    """
    A class used to represent a Thorlabs KPZ101 device.
    
    All methods and functions are implemented separately inside class
    in order to limit functionality.
    
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
    
    disable()
        If device.IsConnected == True, disables the device so that the voltage
        is no longer being output
    enable()
    
    stop()
        
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
    
        # Check Device is being registered by computer
        if DeviceManagerCLI.GetDeviceListSize() < 1:
            raise Exception('No Device Available')
            
        # Created KCubePiezo device
        self.device = KCubePiezo.CreateKCubePiezo(serial_no)
        
        # Verify device is connected past this point
        if not self.device.IsConnected:
            self.device.Connect(serial_no)
            assert self.device.IsConnected is True
        
        self.device.StartPolling(250)  #250ms polling rate
        time.sleep(0.5)
        self.device.EnableDevice()
        time.sleep(0.25)
        
        if not self.device.IsSettingsInitialized():
            self.device.WaitForSettingsInitialized(10000)  # 10 second timeout
            assert self.device.IsSettingsInitialized() is True
        
        # Set the max voltage, jog steps, and current voltage.
        self.max_voltage = self.device.GetMaxOutputVoltage()
        self.jogsteps = self.device.GetJogSteps()
        self.cvoltage = self.device.GetOutputVoltage()
        
        print('Initialized', serial_no)
        
    def getVoltage(self):
        return self.cvoltage
    
    def getVoltageFloat(self, rounding):
        return round(float(self.device.GetOutputVoltage().ToString()), rounding)
    
    def getMaxVoltage(self):
        return self.device.GetMaxOutputVoltage()
        
    def getJogSteps(self):
        # REMEMBER: This is a JogStepStruct OBJECT, not Decimal!!!!
        return self.jogsteps
    
    def isConnected(self):
        return self.device.IsConnected
    
    def update(self):
        # Update the current voltage 
        self.cvoltage = self.device.GetOutputVoltage()
        
    def setZero(self):
        # Set device to zero voltage
        self.device.SetZero()
        
    def setVoltage(self, voltage):
        # Given Decimal 0 <= voltage <= max_voltage, update current voltage of KPZ101 to voltage
        if voltage >= Decimal(0) and voltage <= self.max_voltage:
            self.device.SetOutputVoltage(voltage)
            time.sleep(1)
        
    def setJogSteps(self, new_step):
        # Given Decimal 0 <= new_step <= 10V, update voltage jog step to new_step
        if new_step >= Decimal(0) and new_step <= Decimal(10):
            self.jogsteps.VoltageStepSize = new_step
            self.device.SetJogSteps(self.jogsteps)
            time.sleep(0.25)
        
    def jogVoltage(self, boolean):
        # Given Boolean boolean, jog the voltage by the voltage jog step.
        #  If boolean == True: Increase voltage
        #  If boolean == False: Decrease voltage
        Increase = Settings.ControlSettings.PiezoJogDirection.Increase
        Decrease = Settings.ControlSettings.PiezoJogDirection.Decrease
        if self.cvoltage >= Decimal(0) and self.cvoltage <= self.max_voltage:
            if boolean:
                self.device.Jog(Increase)
                
            else:
                self.device.Jog(Decrease)
                
    def disconnect(self):
        # Disconnect the Piezo Controller, but do not disable it
        if self.device.IsConnected:
            self.device.StopPolling()
            time.sleep(1)
            self.device.Disconnect(False)
        
    def connect(self):        
        # Verify device is connected past this point
        # self.device = KCubePiezo.CreateKCubePiezo(self.serial_no)
        
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
        self.device.DisableDevice()
        time.sleep(0.25)
        
    def enable(self):
        self.device.EnableDevice()
        time.sleep(0.25)
        
    def stop(self):
        self.device.DisableDevice()
        self.device.StopPolling()
        time.sleep(1)
        self.device.Disconnect(False)

class Ui(QtWidgets.QMainWindow):
    
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('gui_v2.ui', self)
        self.stylesheetlist = ['#f6cefc', '#ffbacd', '#fbdd7e', '#fffd74',
                            '#cffdbc', '#bdf6fe']
        self.count = 0
        
        self.setStyleSheet("background-color: #f6cefc;")
        
        self.KPZ101_x = KPZ101(serial_no_x)
        self.KPZ101_y = KPZ101(serial_no_y)
        # self.current_voltage = 0 # Current voltage of x direction piezo
        # self.current_jog_step = 0
        
        ## GUI Buttons for X (Horizontal) Piezo Controller
        self.kpzx = [self.KPZ101_x, self.lcdNumberCVX]
        
        self.buttonMoveLeft.clicked.connect(lambda : self.increaseVoltage(self.kpzx))
        self.buttonMoveRight.clicked.connect(lambda : self.decreaseVoltage(self.kpzx))
        self.lineEditSetVX.returnPressed.connect(lambda : self.setVoltage(self.kpzx, self.lineEditSetVX))
        self.lineEditSetJX.returnPressed.connect(lambda : self.setJogStep(self.kpzx, self.lineEditSetJX, self.lcdNumberCJX))
        self.buttonSetZeroX.clicked.connect(lambda : self.setZero(self.kpzx))
        self.buttonDisconnectX.clicked.connect(lambda : self.disconnectPiezo(self.kpzx, self.buttonDisconnectX, self.buttonConnectX))
        self.buttonConnectX.clicked.connect(lambda : self.connectPiezo(self.kpzx, self.buttonDisconnectX, self.buttonConnectX))
        self.buttonConnectX.hide()
        self.buttonDisableX.clicked.connect(lambda : self.disablePiezo(self.kpzx, self.buttonEnableX, self.buttonDisableX))
        self.buttonEnableX.clicked.connect(lambda : self.enablePiezo(self.kpzx, self.buttonEnableX, self.buttonDisableX))
        self.buttonEnableX.hide()
        self.buttonSwitchX.clicked.connect(lambda : self.switchDirectionX(self.kpzx))

        self.direction_stateX = True
        
        #Set-up jog-steps upon initialization
        jogstepx = float(self.KPZ101_x.getJogSteps().VoltageStepSize.ToString())
        self.lcdNumberCJX.display(jogstepx)

        ## GUI Buttons for Y (Vertical) Piezo Controller
        self.kpzy = [self.KPZ101_y, self.lcdNumberCVY]
        
        self.buttonMoveUp.clicked.connect(lambda : self.increaseVoltage(self.kpzy))
        self.buttonMoveDown.clicked.connect(lambda : self.decreaseVoltage(self.kpzy))
        self.lineEditSetVY.returnPressed.connect(lambda : self.setVoltage(self.kpzy, self.lineEditSetVY))
        self.lineEditSetJY.returnPressed.connect(lambda : self.setJogStep(self.kpzy, self.lineEditSetJY, self.lcdNumberCJY))
        self.buttonSetZeroY.clicked.connect(lambda : self.setZero(self.kpzy))
        self.buttonDisconnectY.clicked.connect(lambda : self.disconnectPiezo(self.kpzy, self.buttonDisconnectY, self.buttonConnectY))
        self.buttonConnectY.clicked.connect(lambda : self.connectPiezo(self.kpzy, self.buttonDisconnectY, self.buttonConnectY))
        self.buttonConnectY.hide()
        self.buttonDisableY.clicked.connect(lambda : self.disablePiezo(self.kpzy, self.buttonEnableY, self.buttonDisableY))
        self.buttonEnableY.clicked.connect(lambda : self.enablePiezo(self.kpzy, self.buttonEnableY, self.buttonDisableY))
        self.buttonEnableY.hide()
        self.buttonSwitchY.clicked.connect(lambda : self.switchDirectionY(self.kpzy))
        
        self.direction_stateY = True
        
        #Set-up jog-steps upon initialization
        jogstepy = float(self.KPZ101_y.getJogSteps().VoltageStepSize.ToString())
        self.lcdNumberCJY.display(jogstepy)

        #====================================================================

        self.actionChangeSerial.triggered.connect(self.openPopup)

        self.timer = QTimer()
        self.timer.start(1000)
        #self.timer.timeout.connect(self.updateBoth)
        self.timer.timeout.connect(lambda : self.update(self.kpzx))
        self.timer.timeout.connect(self.checkJogLimitX)
        self.timer.timeout.connect(lambda : self.update(self.kpzy))
        self.timer.timeout.connect(self.checkJogLimitY)
        
        self.show()
        
    def update(self, device):
        kpz = device[0]
        lcdDisplay = device[1]
        if kpz.isConnected():
            kpz.update()
            current_voltage = kpz.getVoltageFloat(2)
            lcdDisplay.display(current_voltage)
            
        # if current_voltage < 0.1: #make button go away and come back
            # addsa
            # color = self.stylesheetlist[self.count]
            # self.setStyleSheet("background-color: " + color + ";")
            # if self.count < 5:
            #     self.count+=1
            # else:
            #     self.count = 0         
        
    def setZero(self, device):
        kpz = device[0]
        kpz.setZero()
        self.update(device)
        
    def increaseVoltage(self, device):
        # When the button is pressed (& held) the voltage is increased
        #  by intervals of the jogging rate
        kpz = device[0]
        kpz.jogVoltage(True)
        self.update(device)

    def decreaseVoltage(self, device):
        # When the button is pressed (& held) the voltage is decreased
        #  by intervals of the jogging rate
        kpz = device[0]
        kpz.jogVoltage(False)
        self.update(device)
        
    def setVoltage(self, device, lineEditV):
        # When input given, current voltage is set to input
        kpz = device[0]
        current_voltage = Decimal(float(lineEditV.text()))
        kpz.setVoltage(current_voltage)
        self.update(device)
        lineEditV.clear()
        
    def setJogStep(self, device, lineEditJ, lcdCJ):
        # When input given, current jog step is set to input
        kpz = device[0]
        current_jog_step = Decimal(float(lineEditJ.text()))
        kpz.setJogSteps(current_jog_step)
        lcdCJ.display(lineEditJ.text())
        lineEditJ.clear()
        
    def disconnectPiezo(self, device, buttonDisc, buttonCon):
        kpz = device[0]
        kpz.disconnect()
        buttonDisc.hide()
        buttonCon.show()
        
    def connectPiezo(self, device, buttonDisc, buttonCon):
        kpz = device[0]
        kpz.connect()
        buttonDisc.show()
        buttonCon.hide()
        
    def enablePiezo(self, device, buttonEn, buttonDis):
        kpz = device[0]
        kpz.enable()
        buttonEn.hide()
        buttonDis.show()
    
    def disablePiezo(self, device, buttonEn, buttonDis):
        kpz = device[0]
        kpz.disable()
        buttonDis.hide()
        buttonEn.show()
        
    def switchDirectionX(self, device):
        if self.direction_stateX == True:
            self.buttonMoveLeft.clicked.disconnect()
            self.buttonMoveRight.clicked.disconnect()
            self.buttonMoveLeft.clicked.connect(lambda : self.decreaseVoltage(self.kpzx))
            self.buttonMoveRight.clicked.connect(lambda : self.increaseVoltage(self.kpzx))
        else:
            self.buttonMoveLeft.clicked.disconnect()
            self.buttonMoveRight.clicked.disconnect()
            self.buttonMoveLeft.clicked.connect(lambda : self.increaseVoltage(self.kpzx))
            self.buttonMoveRight.clicked.connect(lambda : self.decreaseVoltage(self.kpzx))
        self.direction_stateX = not self.direction_stateX
        
    def switchDirectionY(self, device):
        if self.direction_stateY == True:
            self.buttonMoveUp.clicked.disconnect()
            self.buttonMoveDown.clicked.disconnect()
            self.buttonMoveUp.clicked.connect(lambda : self.decreaseVoltage(self.kpzy))
            self.buttonMoveDown.clicked.connect(lambda : self.increaseVoltage(self.kpzy))
        else:
            self.buttonMoveUp.clicked.disconnect()
            self.buttonMoveDown.clicked.disconnect()
            self.buttonMoveUp.clicked.connect(lambda : self.increaseVoltage(self.kpzy))
            self.buttonMoveDown.clicked.connect(lambda : self.decreaseVoltage(self.kpzy))
        self.direction_stateY = not self.direction_stateY
        
    def checkJogLimitX(self):
        if self.KPZ101_x.isConnected():
            current_voltage = self.KPZ101_x.getVoltage()
            current_jog = self.KPZ101_x.getJogSteps().VoltageStepSize
            max_voltage = self.KPZ101_x.getMaxVoltage()
            if current_voltage <= current_jog:
                if self.direction_stateX:
                    self.buttonMoveRight.setEnabled(False)
                    self.buttonMoveLeft.setEnabled(True)
                else:
                    self.buttonMoveLeft.setEnabled(False)
                    self.buttonMoveRight.setEnabled(True)
            elif current_voltage + current_jog >= max_voltage:
                if self.direction_stateX:
                    self.buttonMoveLeft.setEnabled(False)
                    self.buttonMoveRight.setEnabled(True)
                else:
                    self.buttonMoveRight.setEnabled(False)
                    self.buttonMoveLeft.setEnabled(True)
            else:
                self.buttonMoveRight.setEnabled(True)
                self.buttonMoveLeft.setEnabled(True)
            
    def checkJogLimitY(self):
        if self.KPZ101_y.isConnected():
            current_voltage = self.KPZ101_y.getVoltage()
            current_jog = self.KPZ101_y.getJogSteps().VoltageStepSize
            max_voltage = self.KPZ101_y.getMaxVoltage()
            if current_voltage <= current_jog:
                if self.direction_stateY:
                    self.buttonMoveDown.setEnabled(False)
                    self.buttonMoveUp.setEnabled(True)
                else:
                    self.buttonMoveUp.setEnabled(False)
                    self.buttonMoveDown.setEnabled(True)
            elif current_voltage + current_jog >= max_voltage:
                if self.direction_stateY:
                    self.buttonMoveUp.setEnabled(False)
                    self.buttonMoveDown.setEnabled(True)
                else:
                    self.buttonMoveDown.setEnabled(False)
                    self.buttonMoveUp.setEnabled(True)
            else:
                self.buttonMoveUp.setEnabled(True)
                self.buttonMoveDown.setEnabled(True)
        
    def openPopup(self):
        self.popupWindow = SerialNumberPopup()
        self.popupWindow.show()
    
    def closeEvent(self, event):
        if not self.KPZ101_x.isConnected():
            self.KPZ101_x.connect()
        self.KPZ101_x.stop()
        if not self.KPZ101_y.isConnected():
            self.KPZ101_y.connect()
        self.KPZ101_y.stop()
        print('App closed')
        
class SerialNumberPopup(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('gui_popup_window.ui', self)
        self.setStyleSheet("background-color: #f6cefc;")
        self.lineEditX.returnPressed.connect(self.inputLineEditX)
        self.lineEditY.returnPressed.connect(self.inputLineEditY)
        self.buttonSave.clicked.connect(self.saveSerials)
        self.buttonCancel.clicked.connect(self.close)
        
        self.serialnox = serial_no_x
        self.serialnoy = serial_no_y
        
        self.lineEditX.setText(self.serialnox)
        self.lineEditY.setText(self.serialnoy)
        
    def inputLineEditX(self):
        self.serialnox = self.lineEditX.text()
        print(self.serialnox)
        
    def inputLineEditY(self):
        self.serialnoy = self.lineEditY.text()
        print(self.serialnoy)
        
    def saveSerials(self):
        self.close()
    
        
        
def startGUI():
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()

startGUI()
    
