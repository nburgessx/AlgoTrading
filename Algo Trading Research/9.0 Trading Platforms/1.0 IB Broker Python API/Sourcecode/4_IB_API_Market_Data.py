# -*- coding: utf-8 -*-
"""
Created on Mon May 25, 2020

Modified on Fri Sep 14, 2022

@author: Jay Parmar

@doc: https://interactivebrokers.github.io/tws-api/md_request.html

@goal: Request live data from the TWS
"""

# Import necessary libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from threading import Thread
import time

# Define strategy class - inherits from EClient and EWrapper
class Strategy(EClient, EWrapper):
    
    # Initialize the class - and inherited classes
    def __init__(self):
        EClient.__init__(self, self)

    def tickPrice(self, reqId, tickType, price, attrib):
        """
        Handle ticks from the TWS
        1 : Bid Price
        2 : Ask Price
        6 : Day's High Price
        7 : Day's Low Price
        9 : Yesterday's Close Price
        """
        
        cTime = time.strftime("%H:%M:%S", time.localtime())
        print(f'Id: {reqId}, Time: {cTime} TickType: {tickType}, Price: {price}')
        
        
# -------------------------x-----------------------x---------------------------

# Create object of the strategy class
app = Strategy()

# Connect strategy to IB TWS
app.connect(host='localhost', port=7497, clientId=1)

# Wait for sometime to connect to the server
time.sleep(1)

# Start a separate thread that will receive all responses from the TWS
Thread(target=app.run, daemon=True).start()

print('Is application connected to IB TWS:', app.isConnected())

# Create object for contract
contract = Contract()
contract.symbol = 'AAPL'
contract.secType = 'STK'
contract.exchange = 'SMART'
contract.currency = 'USD'

reqId = 150

# Request market data from the TWS
app.reqMktData(reqId=reqId, 
               contract=contract, 
               genericTickList='', 
               snapshot=False, 
               regulatorySnapshot=False, 
               mktDataOptions=[])

# Sleep for few seconds
time.sleep(10)

# Send request to cancel market data
app.cancelMktData(reqId)

# Disconnect the application
app.disconnect()