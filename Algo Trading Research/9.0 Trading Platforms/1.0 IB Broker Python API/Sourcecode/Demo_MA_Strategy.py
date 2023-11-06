# -*- coding: utf-8 -*-
"""
Created on Fri Nov 13 16:33:33 2020

@author: Jay Parmar

# Read Me:-
- Change the start datetime and end datetime before running this strategy.
- This code shows the intraday implementation of moving average crossover.
- This strategy will fire market orders with its default settings.
- Use the contract that you are familiar with.

# Limitations:-
- This code does not implement fetching real-time tick data. 
- This strategy does not account for positions opened from TWS API.
- This strategy does not close positions at day end.

"""

# Importing necessary libraries
from ibapi.client import EClient # To request various operations
from ibapi.wrapper import EWrapper # To handle responses from IB TWS
from ibapi.contract import Contract # To create contract objects
from ibapi.order import Order # To create order objects
from threading import Thread # To perform threading operation
from time import sleep 
import pandas as pd # To perform data analysis
import talib as ta # To calculate technical indicators
from datetime import datetime # To perform datetime related tasks
import numpy as np # To perform number crunching

# Strategy class that handles all strategy related operations
class Strategy(EClient, EWrapper):
    
    # Initialize method to initialize various parameters
    def __init__(self, sma=10, lma=20, qty=1):
        EClient.__init__(self, self)
        
        # Initializing strategy parameters
        self.sma = sma
        self.lma = lma
        self.qty = qty
        
        # Flag to determine the first position
        self.first_position = True
        
        # Initializing request id with 0
        self.request_id = 0
        
        # Empty dataframe to store historical data 
        self.hist_df = pd.DataFrame(columns=['O', 'H', 'L', 'C', 'V'])
        
        # Empty dictionary to hold temporary data
        self.new_data = {}
        
    # Callback to handle errors
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson = ''):
        super().error(reqId, errorCode, errorString)
        print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString)
        
    # Callback to handle order ids
    def nextValidId(self, orderId):         
        super().nextValidId(orderId)
        self.nextOrderId = orderId
        print('NextValidId:', orderId)
        
    # Callback to handle open order responses
    def openOrder(self, orderId, contract, order, orderState):
        print(f'\nOrder open for {contract} with orderid {orderId}.')
        
    # Callback to handle order statuses
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, \
                    permId, parentIt, lastFillPrice, clientId, whyHeld, \
                    mktCapPrice):
        print(f'\nOrder Status - OrderId: {orderId}, Status: {status}, Filled: {filled}, FilledPrice: {avgFillPrice}')

    # Callback to receive details when orders are executed        
    def execDetails(self, reqId, contract, execution):
        print('\nOrder Executed:', execution.orderId)
        
    # User defined function to generate request ids
    def getReqId(self):
        
        # Increment request id with 1 every time the function is called
        self.request_id += 1
        print('Request Id: {}'.format(self.request_id))
        return self.request_id
    
    # Callback function to get contract details
    def contractDetails(self, reqId, contractDetails):
        self.contract_details = contractDetails
    
    # Callback to receive historical data
    def historicalData(self, reqId, bar):
        
        # Store historical data in the dataframe
        print(reqId, bar)
        self.new_data['O'] = bar.Open
        self.new_data['H'] = bar.High
        self.new_data['L'] = bar.Low
        self.new_data['C'] = bar.Close
        self.new_data['V'] = bar.Volume
        self.hist_df = self.hist_df.append(self.new_data, ignore_index=True)
        
    # Callback to notify historical data received
    def historicalDataEnd(self, reqId, start, end):
        print('Historical data received.')
    
    # User defined function to compute technical indicators
    def computeIndicators(self):
        
        # Compute historical indicators using talib and store it in dataframe
        self.hist_df['sma'] = ta.MA(self.hist_df[:self.sma], matype=0)
        self.hist_df['lma'] = ta.MA(self.hist_df[:self.lma], matype=0)
        print('Computations of indicators completed.')
        
    # User defined function to generate strategy signals
    def generateSignals(self):
        
        # Flags to denote strategy signals
        self.initial_short_position = False
        self.initial_long_position = False
        self.close_prev_long_open_new_short = False
        self.close_prev_short_open_new_long = False
        
        # Generate signals
        self.hist_df['signal'] = np.where(self.hist_df['sma'] > self.hist_df['lma'], 1, -1)
        
        # Fetch last two value values of the signal column
        self.current_signal = self.hist_df['signal'][-1]
        self.prev_signal = self.hist_df['signal'][-2]
        
        # Check if signal is changed
        if self.current_signal != self.prev_signal:
            
            # Check if the short signal is generated
            if self.current_signal == -1:
                # Check if this is the initial position
                if self.first_position == True:
                    # Place order with initial quantity
                    self.initial_short_position = True
                    self.first_position = False
                else:
                    # Place order with the double quantity
                    self.close_prev_long_open_new_short = True
            
            # Check if the long signal is generated
            elif self.current_signal == 1:
                # Check if this is the initial position
                if self.first_position == True:
                    # Place order with initial quantity
                    self.initial_long_position = True
                    self.first_position = False
                else:
                    # Place order with the double quantity
                    self.close_prev_short_open_new_long = True
        else:
            # If last two values are same, we continue the position
            print('Carry forward the previous position')
            
        # Callback function to handle all retrieved positions
        def position(self, account, contract, position, avgCost):
            new_pos_data = {'Account': account,
                            'Symbol': contract.symbol,
                            'SecType': contract.secType,
                            'Position': position, 
                            'AvgCost': avgCost}
            self.pos_df = self.pos_df.append(new_pos_data, ignore_index=True)
            
        # Callback function to denote positions retrieved
        def positionEnd(self):
            print('Latest postions retrieved')
            
        # User defined function to place order based on the strategy signal
        def place_orders(self):
            if self.initial_short_position:
                self.mkt_order.action = 'SELL'
                self.mkt_order.totalQuantity = -self.qty
            elif self.initial_long_position:
                self.mkt_order.action = 'BUY'
                self.mkt_order.totalQuantity = self.qty
            elif self.close_prev_long_open_new_short:
                self.mkt_order.action = 'SELL'
                self.mkt_order.totalQuantity = -self.qty * 2
            elif self.close_prev_short_open_new_long:
                self.mkt_order.action = 'BUY'
                self.mkt_order.totalQuantity = self.qty * 2
            
            self.placeOrder(orderId=self.nextValidId, 
                            contract=self.trading_contract, 
                            order=self.mkt_order)
###############################################################################

# User defined function to build trading contract
def buildContract(symbol, currency, exchange, sec_type):
    contract = Contract()
    contract.symbol = symbol
    contract.currency = currency
    contract.exchange = exchange
    contract.secType = sec_type
    return contract

# User defined function to build market order
def buildMktOrder():
    order = Order()
    order.action = 'BUY'
    order.totalQuantity = 0
    order.orderType = 'MKT'
    return order
###############################################################################

# The following code execute only once per run

# Create a Strategy class object
app = Strategy(sma=10, lma=20, qty=1)

# Connect with TWS
app.connect(host='localhost', port=7497, clientId=11)

sleep(1)

# Start a separate thread that will receive all responses from the TWS
Thread(target=app.run, daemon=True).start()

# Create a trading contract
app.trading_contract = buildContract('EUR', 'USD', 'IDEALPRO', 'CASH')

# Create a default market order
app.mkt_order = buildMktOrder()

sleep(1)

# Define a function that will bind all strategy parts together
def run_strategy():
    
    # Empty dataframe on every iteration
    app.hist_df = app.hist_df.iloc[0:0]
    
    # Request historical data
    app.reqHistoricalData(app.getReqId(), app.trading_contract, '', '1 D', 
                          '1 min', 'TRADES', 0, 1, False, [])
    
    # Wait for sometime to ensure that historical data is downloaded
    sleep(3)
    
    # If historical data is downloaded, proceed further
    if len(app.hist_df) > 0:
        app.computeIndicators()
        app.generateSignals()
        app.placeOrders()
    
    # If historical data is not downloaded, need to intervene.
    # This part can be improvised to handle things in an automated fashion
    else:
        print('Historical data is not available. Please check.')

# run_strategy()
# sleep(30)
# app.disconnect()

###############################################################################

# The following code executes things iteratively

# Define start and end date and time for algo execution
_start_time = '2021-12-29 09:15:00'
_end_time = '2021-12-29 23:30:00'

# Define execution frequency
# 1T = 1 Minute, 3T = 3 Minutes, 5T = 5 Minutes
_frequency = '1T' 

# Define the default time format
tf = '%Y-%m-%d %H:%M:%S'

# Generate timestamps
timestamps = pd.date_range(start=_start_time, 
                           end=_end_time, 
                           freq=_frequency).strftime(tf)

#  Run infinite loop that iterates over the timestamps generated above
while True:
    
    # Get current time
    current_time = datetime.now().strftime(tf)
    
    # If the current time is less than the strategy start time, then wait
    if datetime.strptime(current_time, tf) < datetime.strptime(_start_time, tf):
        print('Wait', current_time)
        sleep(1)
        continue
    
    # If the current time is within strategy run time, execute the algorithm
    elif current_time in timestamps:
        print('Executing algorithm:', current_time)
        run_strategy()
        
    # If the current time is greater than the strategy run time, then exit the execution
    elif datetime.strptime(current_time, tf) > datetime.strptime(_end_time, tf):
        print('Finish. Disconnecting the application:', current_time)
        app.disconnect()
        break
    sleep(1)

