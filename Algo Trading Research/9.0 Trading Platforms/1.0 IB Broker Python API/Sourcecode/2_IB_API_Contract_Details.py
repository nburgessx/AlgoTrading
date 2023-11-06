# -*- coding: utf-8 -*-
"""
Created on Mon May 25, 2020

Modified on Fri Sep 14, 2022

@author: Jay Parmar

@doc: https://interactivebrokers.github.io/tws-api/basic_contracts.html

@goal: Fetch details of a financial instrument

@output_details: https://interactivebrokers.github.io/tws-api/classIBApi_1_1ContractDetails.html
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
        
    # OVERRIDE:        
    # Receives contract details from TWS
    # Defined in EWrapper class
    def contractDetails(self, reqId, contractDetails):
        print('\nReqId: ', reqId, '\nContract Details: ', contractDetails)
    
    # OVERRIDE:
    # Disconnect the app once the contract details are received
    # Overriding the contractDetailsEnd mehtod from EWrapper class
    def contractDetailsEnd(self, reqId):
        print('\nReqId: ', reqId, 'Contract Details Ended.')

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
eu_contract = Contract()

# I intend to trade a forex pair: EUR.USD
eu_contract.symbol = 'EUR'
eu_contract.currency = 'USD'
eu_contract.secType = 'CASH'
eu_contract.exchange = 'IDEALPRO'

# This contract for the call options 
contract = Contract()

# Equity
contract.symbol = "MSFT"
contract.secType = "STK"
contract.currency = "USD"
contract.exchange = "SMART"
contract.primaryExchange = "ISLAND"

# Request contract details - EClient
app.reqContractDetails(reqId=201, contract=eu_contract)
app.reqContractDetails(reqId=202, contract=contract)

# Wait for sometime to receive the response
time.sleep(10)

# Disconnect the app
app.disconnect()

# Equity Index Option
# contract.symbol = "NIFTY50"
# contract.secType = "OPT"
# contract.currency = "INR"
# contract.exchange = "NSE"
# contract.primaryExchange = "NSE"
# contract.lastTradeDateOrContractMonth = '202207'
# contract.strike = 18000
# contract.right = 'C'
# contract.multiplier = '1'

# Equity
# contract = Contract()
# contract.symbol = "MSFT"
# contract.secType = "STK"
# contract.currency = "USD"
# contract.exchange = "SMART"
# contract.primaryExchange = "ISLAND"

# Index
# contract = Contract()
# contract.symbol = 'NIFTY50'
# contract.secType = 'IND'
# contract.currency = 'INR'
# contract.exchange = 'NSE'

# Futures Contract
# contract = Contract()
# contract.symbol = 'ES'
# contract.secType = 'FUT'
# contract.currency = 'USD'
# contract.exchange = 'GLOBEX'
# contract.lastTradeDateOrContractMonth = '202101'

# Options Contract
# contract = Contract()
# contract.symbol = 'GOOG'
# contract.secType = 'OPT'
# contract.exchange = 'SMART'
# contract.currency = 'USD'
# contract.lastTradeDateOrContractMonth = '20201023'
# contract.strike = 1555
# contract.right = 'C'
# contract.multiplier = '100'