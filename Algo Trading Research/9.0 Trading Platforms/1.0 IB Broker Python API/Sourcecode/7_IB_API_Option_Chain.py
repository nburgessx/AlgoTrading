# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 16:12:01 2020

@author: Jay Parmar

@doc: https://interactivebrokers.github.io/tws-api/basic_contracts.html

@goal: Fetch options chain 

@output_details: https://interactivebrokers.github.io/tws-api/classIBApi_1_1ContractDetails.html
"""

# Import necessary libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from threading import Thread
import time

class strategy(EClient, EWrapper):
    
    def __init__(self):
        EClient.__init__(self, self)
        
    def contractDetails(self, reqId, contractDetails):
        cont = contractDetails.contract
        symbol = cont.symbol
        strike = cont.strike
        right = cont.right
        multiplier = cont.multiplier
        exp_date = contractDetails.realExpirationDate
        exchange = cont.exchange
        
        print(symbol, strike, right, multiplier, exp_date, exchange)
        # print('\nReqId: ', reqId, '\nContract Details: ', contractDetails )
        
        self.contracts[cont.strike] = cont
        
    def contractDetailsEnd(self, reqId):
        print('\nReqId: ', reqId, 'Contract Details Ended.')
        
        for k, v in self.contracts:
            print(k, v)
        
    def historicalData(self, reqId, bar):
        print('Req Id:', reqId)
        print(f'Time: {bar.date}, Open: {bar.open}, Close: {bar.close}')
        
    # Display a message once historical data is retreived
    def historicalDataEnd(self, reqId, start, end):
        print('\nHistorical Data Retrieved\n')
        
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

app.contracts = {}

contract = Contract()
contract.symbol = "NIFTY50"
contract.secType = "OPT"
contract.currency = "INR"
contract.exchange = "NSE"
# contract.strike = 19250
contract.lastTradeDateOrContractMonth = '20220428'
contract.right = 'P'

# Request contract details
app.reqContractDetails(reqId=38, contract=contract)

# app.reqHistoricalData(reqId=33, 
#                       contract=contract,
#                       endDateTime='20220419 23:59:59',
#                       durationStr='1 D',
#                       barSizeSetting='3 hours',
#                       whatToShow='MIDPOINT',
#                       useRTH=True,
#                       formatDate=1,
#                       keepUpToDate=False,
#                       chartOptions=[])

# Sleep for few seconds
time.sleep(60)

# Disconnect the strategy
app.disconnect()