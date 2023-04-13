# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 11:17:57 2023

With this program, the aim is to be able to control 2 Piezo Controller devices
with known serial numbers, that are connected to the computer on which this
software is running from. Technically the code can be adjusted in GUI.py 
to run with only 1 Piezo Controller, or possibly more than 2.

Dependencies are the Thorlabs Kinesis software - must be installed for use of
driver (.dll) files, NI-Visa for Piezo Controller connection, as well as 
the ctypes Python package since the Thorlabs software is optimized for C.

NOTE:
-------------
Restart the kernel when you run the code - otherwise the imports get
messed up due to mainly the drivers. PyQt5 can also cause some problems
if the kernel is not restarted.

@author: Anya Dovgal
"""


#%% Package imports for software operation
# Need to check that 'ctypes' package is also installed to environment
# If not, either add via Anaconda package installation system, or run
#    pip install ctypes
# NI-Visa and Thorlabs Kinesis should also be installed and up-to-date

import os
import sys
import json

from PyQt5 import QtWidgets, uic

#from KPZ101 import KPZ101
from GUI import Ui

#%%

def main():
    """ Starts the application for Piezo Controller control.
    """
    startGUI() 
        
        
def startGUI():
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()

if __name__ == '__main__':
    sys.exit(main())
    
