# -*- coding: utf-8 -*-
"""
Created on Fri Mar 31 15:08:15 2023

@author: Anya
"""

class MisMatchSerialError(ValueError):
    """
    Raise this when a saved/inputted serial number does not match the
    serial numbers of devices connected to the computer
    """
    
    def __init__(self, attempt, actual, message = 'The serial numbers do not match'):
        super().__init__(message)
        
        self.attempt = attempt # The serial number that is not recognized
        self.actual = [actual[0], actual[1]] # The devices that are connected
        self.message = message
        
class DeviceCountError(ValueError):
    """
    Raise this when the number of connected devices is less than 2
    """
    
    def __init__(self, count, message = "The number of connected devices is "):
        super().__init__(message + str(count))
        
        self.message = message
        self.count = count