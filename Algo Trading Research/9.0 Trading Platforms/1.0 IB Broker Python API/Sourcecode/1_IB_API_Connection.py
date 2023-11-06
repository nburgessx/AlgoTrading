# -*- coding: utf-8 -*-
"""
Created on Mon May 25, 2020

Modified on Fri Sep 14, 2021

@author: Jay Parmar

@doc: http://interactivebrokers.github.io/tws-api/connection.html

@goal: Connect Python script to TWS
"""

# Import necessary libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from threading import Thread
import time
from datetime import datetime

# Define strategy class - inherits from EClient and EWrapper
class Strategy(EClient, EWrapper):
    
    # Initialize the class - and inherited classes
    def __init__(self):
        # EClient will init EClient and EWrapper and needs self x2
        EClient.__init__(self, self)

    # OVERRIDE: We override the underlying method in IB to print the time in readable format
    # This Callback method is available from the EWrapper class
    def currentTime(self, time): # Method to handle response
        t = datetime.fromtimestamp(time) # Changes the time to human readable format
        print('Current time on server:', t)
        
# -------------------------x-----------------------x---------------------------

# Create object of the strategy class
app = Strategy()

# Connect strategy to IB TWS
# Host can also be IP Address
# Port (telephone number): 7497 = Simulation or 7496 = Live
app.connect(host='localhost', port=7497, clientId=1) # Blue line

# Wait for sometime to connect to the server
time.sleep(1)

# Start a separate thread that will receive all responses from the TWS
Thread(target=app.run, daemon=True).start() # Orange line

print('\nIs application connected to IB TWS:', app.isConnected())

# Example of sending a request to TWS
app.reqCurrentTime()

time.sleep(5)

# Disconnect the app
app.disconnect()


