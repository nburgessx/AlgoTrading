# -*- coding: utf-8 -*-
"""
Created on Mon May 25, 2020

Modified on Fri Sep 14, 2022

@author: Jay Parmar

@doc: https://interactivebrokers.github.io/tws-api/basic_orders.html

@goal: Order placement and cancellation
"""

# Import necessary libraries
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from threading import Timer, Thread
import time

# Define strategy class - inherits from EClient and EWrapper
class Strategy(EClient, EWrapper):
    
    # Initialize the class - and inherited classes
    def __init__(self):
        EClient.__init__(self, self)


    def placeOrder(self, orderId, contract, order):
        print("*** PLACING ORDER ***")
        print(f"orderId {orderId}")
        print(f"contract {contract}")
        super().placeOrder(orderId, contract, order)
        
    def openOrder(self, orderId, contract, order, orderState):
        print(f'\nOrder open for {contract} with orderid {orderId}.')
        
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, \
                    permId, parentIt, lastFillPrice, clientId, whyHeld, \
                    mktCapPrice):
        print(f'\nOrder Status - OrderId: {orderId}, Status: {status}, Filled: {filled}, FilledPrice: {avgFillPrice}')

    # Receive details when orders are executed        
    def execDetails(self, reqId, contract, execution):
        print('\nOrder Executed:', execution.orderId)

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

# Define order id. This is not same as the request id
oid = 226

# Create object for contract
contract = Contract()
contract.symbol = "NVDA"
contract.secType = "STK"
contract.currency = "USD"
contract.exchange = "SMART"
contract.primaryExchange = "ISLAND"

# Create object for order
order = Order()
order.action = 'BUY'
order.totalQuantity = 20000
order.orderType = 'MKT'

# order.lmtPrice = '1.1718'

# Request function
app.placeOrder(orderId=oid, 
               contract=contract, 
               order=order)

# Waiting for 5 seconds
Timer(10, app.cancelOrder, [oid]).start()

# Sleep for few seconds
time.sleep(15)

# Disconnect the application
app.disconnect()
