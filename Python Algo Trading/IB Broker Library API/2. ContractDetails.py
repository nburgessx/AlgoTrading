# -*- coding: utf-8 -*-
"""
Created on Sun Sep 24, 2023

@author: Nicholas Burgess

@doc: https://interactivebrokers.github.io/tws-api/basic_contracts.html

@goal: Fetch contract details for a financial instrument

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
# Ports: 7497 = Demo IB Acct or 7496 = Live Trading Acct
app.connect(host='localhost', port=7497, clientId=1)

# Wait for sometime to connect to the server
time.sleep(1)

# Start a separate thread that will receive all responses from the TWS
# Use daemon so thread persists and terminates correctly
Thread(target=app.run, daemon=True).start()

# Print Connection Status
print('\n *** Application Connection Status to IB TWS ***')
print('Connection Established:', app.isConnected(), "\n")

# Create Equity Contract
# Equity
contract1 = Contract()
contract1.symbol = "MSFT"
contract1.secType = "STK"
contract1.currency = "USD"
contract1.exchange = "SMART"
contract1.primaryExchange = "ISLAND"

# Equity
contract2 = Contract()
contract2.symbol = "MSFT"
contract2.secType = "STK"
contract2.currency = "USD"
contract2.exchange = "SMART"
contract2.primaryExchange = "ISLAND"

# Request contract details - EClient
app.reqContractDetails(reqId=101, contract=contract1)
app.reqContractDetails(reqId=102, contract=contract2)

# Wait for sometime to receive the response
time.sleep(10)

# Disconnect the app
app.disconnect()

# Other Contract Types

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