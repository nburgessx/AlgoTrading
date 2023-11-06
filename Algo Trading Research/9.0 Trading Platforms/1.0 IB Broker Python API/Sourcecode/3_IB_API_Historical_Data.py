# -*- coding: utf-8 -*-
"""
Created on Mon May 25, 2020

Modified on Fri Sep 14, 2022

@author: Jay Parmar

@doc: http://interactivebrokers.github.io/tws-api/historical_bars.html

@goal: Fetch historical data of a financial instrument
"""

# Import necessary libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from threading import Thread
import pandas as pd
import time

# Define strategy class - inherits from EClient and EWrapper
class Strategy(EClient, EWrapper):
    
    # Initialize the class - and inherited classes
    def __init__(self):
        EClient.__init__(self, self)
        self.df = pd.DataFrame(columns=['Time', 'Open', 'Close'])
           
    # Receive historical bars from TWS
    def historicalData(self, reqId, bar):
        print('Req Id:', reqId)
        dictionary = {'Time':bar.date,'Open': bar.open, 'Close': bar.close}
        self.df = self.df.append(dictionary, ignore_index=True)
        print(f'Time: {bar.date}, Open: {bar.open}, Close: {bar.close}')
        
    # Display a message once historical data is retreived
    def historicalDataEnd(self, reqId, start, end):
        print('\nHistorical Data Retrieved\n')
        print(self.df.head())
        self.df.to_csv('Historical_data.csv')
        
    
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
contract.symbol = 'GOOG'
contract.secType = 'STK'
contract.exchange = 'SMART'
contract.currency = 'USD'

# Request for historical data - EClient
app.reqHistoricalData(reqId=33, 
                      contract=contract,
                      endDateTime='20230924 23:59:59 UTC',
                      durationStr='7 D',
                      barSizeSetting='1 min',
                      whatToShow='MIDPOINT',
                      useRTH=True,
                      formatDate=1,
                      keepUpToDate=False,
                      chartOptions=[])

# Wait for sometime to receive the response
time.sleep(5)

app.cancelHistoricalData(33)

# Disconnect the app
app.disconnect()

