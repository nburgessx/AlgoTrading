# -*- coding: utf-8 -*-
"""
Created on Sun Sep 24, 2023

@author: Nicholas Burgess

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
        # EClient will init EClient and EWrapper and needs self arg x2
        EClient.__init__(self, self)

    # OVERRIDE: Override IB Method to Print Response
    # This callback method is available from the EWrapper class
    def currentTime(self, time): # Method to handle response
        t = datetime.fromtimestamp(time)
        print('Current time on server:', t)
        
# -------------------------x-----------------------x---------------------------

# Create instance of Strategy class
app = Strategy()

# Connect strategy to IB TWS
# Ports: 7497 = Demo IB Acct or 7496 = Live Trading Acct
app.connect(host='localhost', port=7497, clientId=1) # Blue line
time.sleep(2) # Pause to establish connection

# Start a separate thread that will receive all responses from the TWS
# Use daemon so thread persists and terminates correctly
Thread(target=app.run, daemon=True).start()

# Print Connection Status
print('\n *** Application Connection Status to IB TWS ***')
print('Connection Established:', app.isConnected(), "\n")

# Send a request to TWS and pause briefly to read results
app.reqCurrentTime()
time.sleep(5)

# Disconnect App
app.disconnect()


