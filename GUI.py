# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 15:54:26 2023

This class encompasses the GUI creation and usage for Piezo Control, 
initialized in the main program.

The .ui files were created and designed mainly using the PyQt5 Designer
Application, and can be viewed/edited in said application as well for
ease of use.

@author: Anya Dovgal
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
from Exceptions import MisMatchSerialError, DeviceCountError

class Ui(QtWidgets.QMainWindow):
    """
    The main GUI for Piezo control, with all graphics designed in the 
    PyQt Designer application. 
    
    Attributes
    ----------
    KPZ101_x : KPZ101 Object
        For horizontal movement
    KPZ101_y : KPZ101 Object
        For vertical movement
    timer : QTimer
        Mainly for updating the voltage display so that it accurately
        reflects the real-time voltage of the piezo devices
    popupWindow : QWidget
        The pop-up window to help users change the connected piezo device
        in the software
    errorWindow : QWidget
        The error window that will come up if an error occurs, and
        prompt users to either fix the error or quit the software
    
    Methods
    --------
    setupConnections()
        Sets up the connections between GUI buttons/etc. and the helper
        methods in the class for controlling the device.
    resetConnections()
        Removes connections between buttons and methods to avoid issues when
        re-initializing the KPZ devices.
    loadSerials()
        Retrieves the saved KPZ101 serial numbers from the reference json file
    saveSerials()
        Helper method for saveFromPopup(), saves the newly inputted serial
        numbers to the reference json file
    initializeKPZs(serial_x = None, serial_y = None)
        If serial_x & serial_y = None, then initialize the KPZs from the
        saved serial number. This method is also called to test that the serial
        numbers are valid and the KPZs WILL initialize
    update(device)
        Updates the GUI panel for data from device
    setZero(device)
        Sets the voltage of device to zero
    increaseVoltage(device)
        Jogs the voltage of device up
    decreaseVoltage(device)
        Jogs the voltage of device down
    setVoltage(device)
        Sets the voltage of the device to the inputted value
    setJogStep(device)
        Sets the voltage jogging step of the device to the inputted value
    disconnectPiezo(device)
        Disconnects the device from the computer
    connectPiezo(device)
        Connects the device to the computer
    disablePiezo(device)
        Disables the device voltage output
    enablePiezo(device)
        Enables the device voltage output
    switchDirectionX/Y()
        Switches the d-pad direction to jogging step direction, to improve
        usability
    checkJogLimitX/Y()
        Helper function for switchDirectionX/Y()
    openPopup()
        Open the pop-up window
    saveFromPopup()
        Try to initialize the KPZs, and if working
    closeEvent()
        Adds a check that all of the devices are disconnected & disabled
        before software is closed.
    """
    def __init__(self):
        """
        Initializes the GUI, loads the saved serial numbers from the saved
        json file, and starts up the corresponding KPZ 101 devices.
        """
        super(Ui, self).__init__()
        uic.loadUi('gui_v2.ui', self)
        self.popupWindow = None # Place-holder for the pop-up window
        self.errorWindow = None
        self.KPZ101_x = None
        self.KPZ101_y = None
        
        #self.setStyleSheet("background-color: #f6cefc;")
        
        self.loadSerials()
        self.initializeKPZs()
        self.timer = QTimer()
        self.setupConnections()
        
        self.show()
        
    def setupConnections(self):
        """
        Connects the GUI widgets to the class helper methods, for each device
        that is currently connected to the computer/ software.
        """
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

        #===========================================================

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

        self.timer.start(1000)
        self.timer.timeout.connect(lambda : self.update(self.kpzx))
        self.timer.timeout.connect(self.checkJogLimitX)
        self.timer.timeout.connect(lambda : self.update(self.kpzy))
        self.timer.timeout.connect(self.checkJogLimitY)
        
    def resetConnections(self):
        """
        Disconnects a few key widgets from the helper methods - this method
        is necessary because if the KPZ serial numbers are changed/
        're-setup', then the GUI widgets may not work properly without
        disconnecting and then re-connecting them
        """
        self.timer.disconnect()
        
        self.buttonMoveLeft.disconnect()
        self.buttonMoveRight.disconnect()
        self.lineEditSetVX.disconnect()
        self.lineEditSetJX.disconnect()
        self.buttonSwitchX.disconnect()
        
        self.buttonMoveUp.disconnect()
        self.buttonMoveDown.disconnect()
        self.lineEditSetVY.disconnect()
        self.lineEditSetJY.disconnect()
        self.buttonSwitchY.disconnect()
    
    def loadSerials(self):
        """
        Loads the serial numbers that are saved to the software
        """
        with open('saved_serial_numbers.json', 'r') as openfile:
            json_object = json.load(openfile)
        
        self.serial_x = json_object['serialX']
        self.serial_y = json_object['serialY']
        
        openfile.close()
        
    def saveSerials(self, serial_x, serial_y):
        """
        Changes the saved serial numbers to the newly inputted/ connected ones
        """        
        dictionary = {'serialX' : serial_x,
                      'serialY' : serial_y}

        with open("saved_serial_numbers.json", "w") as outfile:
            json.dump(dictionary, outfile)
            
        self.serial_x = serial_x
        self.serial_y = serial_y
        
    def initializeKPZs(self, serial_x = None, serial_y = None):
        """
        If no serial numbers are specified, attempts to initialize the KPZs for
        the saved numbers. Otherwise, attempts to initialize the KPZs for the
        inputted numbers.
        
        If either a MisMatchSerialError or a DeviceCountError occur, the user
        will be prompted via pop-up to fix the problem (either close app and
        make sure devices are connected, or change the serial numbers)

        Parameters
        ----------
        serial_x : String, optional
            DESCRIPTION. The default is None.
        serial_y : String, optional
            DESCRIPTION. The default is None.
        """
        if serial_x == None:
            serial_x = self.serial_x
        if serial_y == None:
            serial_y = self.serial_y
        
        self.isPopupOpen = False
        
        try:
            temp_x = KPZ101(serial_x)
            temp_y = KPZ101(serial_y)
            
            self.KPZ101_x = None
            self.KPZ101_y = None
            
            self.KPZ101_x = temp_x
            self.KPZ101_y = temp_y
        
        except ValueError as e:
            """
            This section can possibly be expanded for error handling.
            """
            # self.isPopupOpen = True
            print(e.message)
            if type(e) == MisMatchSerialError: # If the recorded serial # is not right
                attempt = e.attempt # The serial number that is not connected
                actual = e.actual # The serial numbers that are connected
                # print('I have reached here')
                # self.openSerialErrorPopup()
            
            elif type(e) == DeviceCountError: # If the connected devices is < 2
                count = e.count # Num. of devices actually connected
                # self.openCountErrorPopup()
                # print('I have reached here')
                
        # while self.isPopupOpen == True:
        #     pass
        
    def update(self, device):
        """
        Every 1000 milliseconds, the program 'updates', retrieving the voltage
        data from the kpz and displays it on the gui. It also updtes when
        the voltage is jogged/set.
        
        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        """
        kpz = device[0]
        lcdDisplay = device[1]
        if kpz.isConnected():
            kpz.update()
            current_voltage = kpz.getVoltageFloat(2)
            lcdDisplay.display(current_voltage)   
        
    def setZero(self, device):
        """
        Sets the KPZ voltage to 'zero'

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        """
        kpz = device[0]
        kpz.setZero()
        self.update(device)
        
    def increaseVoltage(self, device):
        """
        When the button is pressed (& held) the voltage is increased by
        intervals of the jogging rate

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        """
        kpz = device[0]
        kpz.jogVoltage(True)
        self.update(device)

    def decreaseVoltage(self, device):
        """
        When the button is pressed (& held) the voltage is decreased by
        intervals of the jogging rate

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        """
        kpz = device[0]
        kpz.jogVoltage(False)
        self.update(device)
        
    def setVoltage(self, device, lineEditV):
        """
        When an input is given, the current voltage of the device is set to
        the input

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        lineEditV : QWidgets.QLineEdit
            The line editor where the desired voltage is inputted.
        """
        kpz = device[0]
        current_voltage = Decimal(float(lineEditV.text()))
        kpz.setVoltage(current_voltage)
        self.update(device)
        lineEditV.clear()
        
    def setJogStep(self, device, lineEditJ, lcdCJ):
        """
        When an input is given, the current jog step is set to the input
        and the lcd display is updated

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        lineEditJ : QWidgets.QLineEdit
            The line editor where the desired jogging step is inputted.
        lcdCJ : QWidgets.QLCDNumber
            The lcd display for the current jogging step.
        """
        current_jog_step = Decimal(float(lineEditJ.text()))
        kpz = device[0]
        kpz.setJogSteps(current_jog_step)
        lcdCJ.display(kpz.getJogStepsFloat(2))
        lineEditJ.clear()
        
    def disconnectPiezo(self, device, buttonDisc, buttonCon):
        """
        Upon pushing the button, the KPZ is disconnected from the software
        and the button is replaced with a connection button

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        buttonDisc : QWidgets.QPushButton
            The 'disconnect' button, for disconnecting the device.
        buttonCon : QWidgets.QPushButton
            The 'connect' button, for re-connecting the device.
        """
        kpz = device[0]
        kpz.disconnect()
        buttonDisc.hide()
        buttonCon.show()
        
    def connectPiezo(self, device, buttonDisc, buttonCon):
        """
        Upon pushing the button, the KPZ is resconnected from the software
        and the button is replaced with a disconnection button

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        buttonDisc : QWidgets.QPushButton
            The 'disconnect' button, for disconnecting the device.
        buttonCon : QWidgets.QPushButton
            The 'connect' button, for re-connecting the device.
        """
        kpz = device[0]
        kpz.connect()
        buttonDisc.show()
        buttonCon.hide()
        
    def enablePiezo(self, device, buttonEn, buttonDis):
        """
        Upon pushing the button, the KPZ voltage output is enabled
        and the button is replaced with a disable button

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        buttonEn : QWidgets.QPushButton
            The 'enable' button, for enabling the device output.
        buttonDis : QWidgets.QPushButton
            The 'disable' button, for disabling the device output.
        """
        kpz = device[0]
        kpz.enable()
        buttonEn.hide()
        buttonDis.show()
    
    def disablePiezo(self, device, buttonEn, buttonDis):
        """
        Upon pushing the button, the KPZ voltage output is disabled
        and the button is replaced with a enable button

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        buttonEn : QWidgets.QPushButton
            The 'enable' button, for enabling the device output.
        buttonDis : QWidgets.QPushButton
            The 'disable' button, for disbaling the device output.
        """
        kpz = device[0]
        kpz.disable()
        buttonDis.hide()
        buttonEn.show()
        
    def switchDirectionX(self, device):
        """
        This method is mainly for user-friendliness.
        Essentially, it lets the user map the d-pad direction to the real
        motion, or camera direction. This lets the program be used more easily.

        Parameters
        ----------
        device : [KPZ101, QWidgets.QLCDNumber]
            The KPZ101 and corresponding voltage lcd display
        """
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
        """
        Same as above, but for Y direction.
        """
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
        """
        This is a helper method for the jogging functions, and will enable/
        disable the d-pad arrow buttons.
        """
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
        """
        (Same as above, but for Y direction)
        This is a helper method for the jogging functions, and will enable/
        disable the d-pad arrow buttons.
        """
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
        """
        Opens the serial number adjustment pop-up window.
        """
        self.popupWindow = SerialNumberPopup()
        self.popupWindow.setSerials(self.serial_x, self.serial_y)
        self.popupWindow.saveClicked.connect(self.saveFromPopup)
        # Set the main window to pause while the pop-up is open, then to 
        #   re-start when the pop-up closes
        self.timer.stop()
        self.popupWindow.setCloseEvent(lambda : self.timer.start(1000))
        self.popupWindow.show()
        
    ##============================================
    ## An attempt to have errors handled properly in the GUI.
    
    # def openCountErrorPopup(self):
    #     self.errorWindow = DeviceCountErrorPopup()
    #     self.errorWindow.setCloseEvent(self.close())
    #     self.errorWindow.switchPopupOpenStatus(self.setPopupClose)
    #     self.errorWindow.show()
        
    # def openSerialErrorPopup(self):
    #     self.errorWindow = SerialErrorPopup()
    #     self.errorWindow.setCloseEvent(self.close())
    #     self.errorWindow.show()
        
    # def setPopupClose(self):
    #     self.isPopupOpen = False
        
    def saveFromPopup(self, new_serials):
        """
        If the new serial numbers inputted by the user don't match the
        saved serial numbers in order, then the connected KPZs are stopped
        and disconnected, then the new numbers are initialized and the 
        json file is re-written.
        
        NOTE:
        ------
            In it's current state, this method is really only useful for
            switching the currently connected x piezo to y, and vice versa. 
            
            Ideally, the functionality would be improved so that this window
            may be used during the startup sequence, in the case of an error.

        Parameters
        ----------
        new_serials : List(String)
            DESCRIPTION.
        """
        serials = [self.KPZ101_x.getSerial(), self.KPZ101_y.getSerial()]
       # for i in range(2):
       #     if new_serials[i] != serials[i]:
        if new_serials != serials:
            self.KPZ101_x.stop()
            self.KPZ101_y.stop()
            
            self.initializeKPZs(new_serials[0], new_serials[1])
            self.resetConnections()
            self.setupConnections()
            
        self.saveSerials(new_serials[0], new_serials[1])
        """
        basically if new[i] != old[i], first disconnect (if connected)
        & stop old[i] completely, then try to create a new KPZ101().
        i = 0 replaces x, 1 replaces y. Then, re-write the json
        with the serial #s that are currently attached.
        """

    
    def closeEvent(self, event):
        """
        Stops the devices completely upon closing of the window.
        """
        if not self.KPZ101_x.isConnected():
            self.KPZ101_x.connect()
        self.KPZ101_x.stop()
        if not self.KPZ101_y.isConnected():
            self.KPZ101_y.connect()
        self.KPZ101_y.stop()
        event.accept()
        print('App closed')
        
class SerialNumberPopup(QtWidgets.QWidget):
    """
    The Widget class for the popup to prompt a change in connected piezo
    to the software
    
    Attributes
    ----------
    serial_x : String
        The inputted 'y direction' serial number
    serial_y : String
        The inputted 'x direction' serial number
    
    Methods
    --------
    setCloseEvent(fnc)
        Have a helper function from Ui() elapse upon closing the popup
    setSerials(serial_x, serial_y)
    inputLineEditX/Y()
    saveSerials()
    """
    
    saveClicked = QtCore.pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        uic.loadUi('gui_popup_window.ui', self)
        
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
        
        
# class SerialErrorPopup(QtWidgets.QWidget):
    
#     closeWindow = QtCore.pyqtSignal(list)
    
#     def __init__(self):
#         super().__init__()
#         uic.loadUi('serialnumbererror_popup.ui', self)
        
#         self.changeButton.clicked.connect(self.changeSerial)
#         self.quitButton.clicked.connect(self.quitPopup)
        
#     def setCloseEvent(self, fnc):
#         self.extraEvent = fnc
        
#     def changeSerial(self):
#         """
#         If the change serial # button is pressed, the serial number popup
#         will open.
#         """
#         return None
    
#     def quitPopup(self):
#         """
#         If the quit button is pressed, the entire application closes/
#         shuts down
#         """
#         return None
    
#     def closeEvent(self, event):
#         self.extraEvent()
#         event.accept()
    
    
# class DeviceCountErrorPopup(QtWidgets.QWidget):

#     def __init__(self):
#         super().__init__()
#         uic.loadUi('devicecounterror_popup.ui', self)
        
#     def setCloseEvent(self, fnc):
#         self.extraEvent = fnc
        
#     def switchPopupOpenStatus(self, fnc):
#         self.setStatus = fnc
        
#     def closeEvent(self, event):
#         """
#         Upon closing the popup, the entire application closes/ shuts down 
#         as well
#         """
#         self.extraEvent()
#        # self.setStatus()
#         event.accept()