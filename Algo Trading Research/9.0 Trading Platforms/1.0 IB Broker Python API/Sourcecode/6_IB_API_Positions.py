# -*- coding: utf-8 -*-
"""
Created on Tue Jun 2, 2020

Modified on Fri Sep 14, 2022

@author: Jay Parmar

@doc: http://interactivebrokers.github.io/tws-api/positions.html

@goal: Fetch positions from the TWS
"""

# Import necessary libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from threading import Thread
import time

# Define strategy class - inherits from EClient and EWrapper
class strategy(EClient, EWrapper):
    
    # Initialize the class - and inherited classes
    def __init__(self):
        EClient.__init__(self, self)
        
    # Receive the positions from the TWS
    def position(self, account, contract, position, avgCost):
        print(f'\nAccount: {account} \nContract: {contract.localSymbol}')
        print(f'Position: {position} \nAvg Cost: {avgCost}')
        
    # Display message once the positions are retrieved
    def positionEnd(self):
        print('\nPositions Retrieved.')
        
# -------------------------x-----------------------x---------------------------

# Create object of the strategy class
app = strategy()

# Connect strategy to IB TWS
app.connect(host='localhost', port=7496, clientId=1)

# Wait for sometime to connect to the server
time.sleep(1)

# Start a separate thread that will receive all responses from the TWS
Thread(target=app.run, daemon=True).start()

print('Is application connected to IB TWS:', app.isConnected())

# Request positions from the TWS
app.reqPositions()

# Sleep for few seconds
time.sleep(5)

# Disconnect the strategy
app.disconnect()