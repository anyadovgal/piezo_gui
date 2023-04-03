# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 15:54:26 2023

This class encompasses the GUI creation and usage for Piezo Control, 
initialized in the main program.

The .ui files were created and designed mainly using the PyQt5 Designer
Application, and can be viewed/edited in said application as well for
ease of use.

@author: Anya
"""
import os
import time
import sys
import clr
import json

from System import Decimal  # necessary for real world units

from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtCore import QTimer

from KPZ101 import KPZ101
from Exceptions import *

class Ui(QtWidgets.QMainWindow):
    
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('gui_v2.ui', self)
        self.popupWindow = None # Place-holder for the pop-up window
        self.stylesheetlist = ['#f6cefc', '#ffbacd', '#fbdd7e', '#fffd74',
                            '#cffdbc', '#bdf6fe']
        self.count = 0
        
        self.setStyleSheet("background-color: #f6cefc;")
        
        self.loadSerials()
        self.initializeKPZs()

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
        jogstepx = float(self.KPZ101_x.getJogSteps().ToString())
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
        jogstepy = float(self.KPZ101_y.getJogSteps().ToString())
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
        self.timer.timeout.connect(self.testingUpdate)
        
        self.show()
        
    def loadSerials(self):
        with open('saved_serial_numbers.json', 'r') as openfile:
            json_object = json.load(openfile)
         
        self.serial_x = json_object['serialX']
        self.serial_y = json_object['serialY']
        
    def initializeKPZs(self, serial_x = None, serial_y = None):
        if serial_x == None:
            serial_x = self.serial_x
        if serial_y == None:
            serial_y = self.serial_y
        # try:
        #     assert (self.serial_x.isnumeric() & (len(self.serial_x) == 8))
        #     assert (self.serial_y.isnumeric() & (len(self.serial_y) == 8))
        # except:
        #     print('Need to set-up both KPZ101 serial numbers')
        
        try:
            self.KPZ101_x = KPZ101(serial_x)
            self.KPZ101_y = KPZ101(serial_y)
        except ValueError as e:
            if e == MisMatchSerialError: # If the recorded serial # is not right
                attempt = e.attempt # The serial number that is not connected
                actual = e.actual # The serial numbers that are connected
            
            elif e == DeviceCountError: # If the connected devices is < 2
                count = e.count # Num. of devices actually connected
            print(e.message)
        
    def testingUpdate(self):
        color = self.stylesheetlist[self.count]
        self.setStyleSheet("background-color: " + color + ";")
        if self.count < 5:
            self.count+=1
        else:
            self.count = 0 
        
    def update(self, device):
        kpz = device[0]
        lcdDisplay = device[1]
        if kpz.isConnected():
            kpz.update()
            current_voltage = kpz.getVoltageFloat(2)
            lcdDisplay.display(current_voltage)   
        
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
            current_jog = self.KPZ101_x.getJogSteps()
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
            current_jog = self.KPZ101_y.getJogSteps()
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
        self.popupWindow.setSerials(self.serial_x, self.serial_y)
        self.popupWindow.saveClicked.connect(self.saveFromPopup)
        # Set the main window to pause while the pop-up is open, then to 
        #   re-start when the pop-up closes
        self.timer.stop()
        self.popupWindow.setCloseEvent(lambda : self.timer.start(1000))
        self.popupWindow.show()
        
    def saveFromPopup(self, new_serials):
        serials = [self.KPZ101_x.getSerial(), self.KPZ101_y.getSerial()]
        # for i in range(2):
        #     if new_serials[i] != serials[i]:
        #         self.KPZ101_x.stop()
        #         self.KPZ101_y.stop()
        #         self.initializeKPZs(new_serials[0], new_serials[1])
        #         print(new_serials)
        """
        basically if new[i] != old[i], first disconnect (if connected)
        & stop old[i] completely, then try to create a new KPZ101().
        i = 0 replaces x, 1 replaces y. Then, re-write the json
        with the serial #s that are currently attached.
        """
                
        # TODO : save the new serial numbers, re-initialize the kpzs
        return None
    
    def closeEvent(self, event):
        if not self.KPZ101_x.isConnected():
            self.KPZ101_x.connect()
        self.KPZ101_x.stop()
        if not self.KPZ101_y.isConnected():
            self.KPZ101_y.connect()
        self.KPZ101_y.stop()
        print('App closed')
        
class SerialNumberPopup(QtWidgets.QWidget):
    saveClicked = QtCore.pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        uic.loadUi('gui_popup_window.ui', self)
        self.setStyleSheet("background-color: #f6cefc;")
        
        onlyInt = QtGui.QIntValidator()
        onlyInt.setRange(0, 99999999)
        
        self.lineEditX.editingFinished.connect(self.inputLineEditX)
        self.lineEditX.setValidator(onlyInt)
        self.lineEditY.editingFinished.connect(self.inputLineEditY)
        self.lineEditY.setValidator(onlyInt)
        self.buttonSave.clicked.connect(self.saveSerials)
        self.buttonCancel.clicked.connect(self.close)
    
    def setCloseEvent(self, fnc):
        self.extraEvent = fnc
    
    def setSerials(self, serial_x, serial_y):
        self.serial_x = serial_x
        self.serial_y = serial_y
        
        self.lineEditX.setText(self.serial_x)
        self.lineEditY.setText(self.serial_y)
        
    def inputLineEditX(self):
        self.serial_x = self.lineEditX.text()
        
    def inputLineEditY(self):
        self.serial_y = self.lineEditY.text()
        
    def saveSerials(self):
        new_serials = [self.lineEditX.text(), self.lineEditY.text()]
        self.saveClicked.emit(new_serials)
        self.close()
        
    def closeEvent(self, event):
        self.extraEvent()
        event.accept()