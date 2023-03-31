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


@author: Anya
"""

# TODO: Check whether it is worth accounting for the 0.05,6V voltage difference

#%% Package imports for software operation
# Need to check that 'ctypes' package is also installed to environment
# If not, either add via Anaconda package installation system, or run
#    pip install ctypes
# NI-Visa and Thorlabs Kinesis should also be installed and up-to-date

import os
import sys
import json

from PyQt5 import QtWidgets, uic

from KPZ101 import KPZ101
from GUI import *
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
        
        
def startGUI():
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()

startGUI()
    
