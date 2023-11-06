# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 20:21:05 2021

Modified on Tue Sep 21 10:26:35 2021

@author: JAY

@goal: To trade assets on an intraday basis using Bollinger bands
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from time import sleep
from threading import Thread
from datetime import datetime as dt
from datetime import timedelta
import pandas as pd
import warnings
import sys
import traceback

warnings.filterwarnings('ignore')


class Strategy(EClient, EWrapper):
    
    def __init__(self):
        EClient.__init__(self, self)
        
        # Empty dataframe to store historical data
        self.df = pd.DataFrame(columns=['t', 'o', 'h', 'l', 'c', 'v'])
        
        # Empty dictionary to hold resampled data
        self.resampled_data = {}
        
        # Initializing request id with 0
        self.request_id = 0
        
        # Initialize initial position
        self.initial_position = False
        
        # Initialize current position
        # 0 = No position
        # 1 = Long position
        # -1 = Short position
        self.current_position = 0
        self.new_signal = 0
        
        self.current_date = dt.now().strftime('%Y%m%d')
        
        # Define a dataframe to store tick data
        self.tick_df = pd.DataFrame(columns=['time', 'last_price'])
        
       
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson = ''):
        """
        Print only those errors which are generated by the strategy.

        Parameters
        ----------
        reqId : integer
            Request id by which the error is generated.
        errorCode : integer
            Contains the error code.
        errorString : str
            Contains the error description.

        Returns
        -------
        None.

        """
        if reqId == -1:
            pass
        else:
            print('ERROR', 'ReqId:', reqId, 'Code:', errorCode, 'Error:', errorString)
            
    
    def historicalData(self, reqId, bar):
        """
        Handles the historical data requests.

        Parameters
        ----------
        reqId : integer
            Request id of the request.
        bar : TYPE
            Historical bar

        Returns
        -------
        None.

        """
        new_data_dict = {'t' : bar.date, 
                         'o' : bar.open, 
                         'h' : bar.high,
                         'l' : bar.low,
                         'c' : bar.close,
                         'v' : bar.volume
                      }
        
        self.df = self.df.append(new_data_dict, ignore_index=True)
        
    def historicalDataEnd(self, reqId, start, end):
        print('Historical data retrieved.')
    
    def tickPrice(self, reqId, tickType, price, attrib):
        cTime = dt.now().strftime(self.tf)
        
        # Adding last price to the tick dataframe
        if tickType == 4:
            self.current_price = price
            
            new_data = {'time': cTime,
                        'last_price': price}
            
            self.tick_df = self.tick_df.append(new_data, ignore_index=True)
    
    def resample_data(self):
        self.previous_time = dt.strptime(self.current_time, self.tf) - timedelta(minutes=self.resampling_frequency)
        self.previous_time = self.previous_time.strftime(self.tf)
                
        self.tick_df['time'] = pd.to_datetime(self.tick_df['time'])
        
        self.temp_data = self.tick_df[(self.tick_df['time'] > self.previous_time) & (self.tick_df['time'] < self.current_time)]
        
        
        self.temp_data.set_index(self.temp_data['time'], inplace=True)
        self.temp_data.index = pd.to_datetime(self.temp_data.index)
        self.temp_data.drop(columns=['time'], inplace=True)
        
        self.resampled_data['t'] = self.current_time
        self.resampled_data['o'] = self.temp_data.resample(self.timestamps_frequency).agg('first').iloc[-1, 0]
        self.resampled_data['h'] = self.temp_data.resample(self.timestamps_frequency).agg('max').iloc[-1, 0]
        self.resampled_data['l'] = self.temp_data.resample(self.timestamps_frequency).agg('min').iloc[-1, 0]
        self.resampled_data['c'] = self.temp_data.resample(self.timestamps_frequency).agg('last').iloc[-1, 0]
        self.resampled_data['v'] = 0
        
        self.df = self.df.append(self.resampled_data, ignore_index=True)
    
    def compute_indicators(self):
        
        # Fetch the last n data points to compute technical indicators
        self.data = self.df.iloc[-self.ma_period:].copy()
        
        # Calculate mean and and standard deviation
        self.ma = self.data['c'].mean()
        self.stddev = self.data['c'].std()
        
        # Compute upper and lower Bollinger bands
        self.upper_band = self.ma + self.stddev * self.std_num
        self.lower_band = self.ma - self.stddev * self.std_num
    
    
    def generate_signals(self):
        
        # new_signal = -1, 1, 0
        # current_position = 0 or 1
        
        print('Current Position:', self.current_position)
        
        # Generate short enter signal
        if self.current_price > self.upper_band:
            if self.current_position == 0:
                self.new_signal = -1
        
        # Generate long enter signal
        if self.current_price < self.lower_band:
            if self.current_position == 0:
                self.new_signal = 1
                
        # Generate long exit signal
        if self.current_price > self.ma:
            if self.current_position == 1:
                self.new_signal = 0
                
        # Generate short exit signal
        if self.current_price < self.ma:
            if self.current_position == -1:
                self.new_signal = 0
            
        print('New signal:', self.new_signal)
    
    
    def place_order(self):
        
        # If a new trading signal is different than the current position, take 
        # a new position or update the exisiting one
        if self.new_signal != self.current_position:
            
            if self.new_signal == 1:
                self.order.action = 'BUY'
                print('Entering a long position')
            
            if self.new_signal == -1:
                self.order.action = 'SELL'
                print('Entering a short position')
            
            if self.new_signal == 0:
            
                if self.current_position == 1:
                    self.order.action = 'SELL'
                    print('Exiting the long position')
                
                if self.current_position == -1:
                    self.order.action = 'BUY'
                    print('Exiting the short position')
                        
            
            self.order.limit_price = self.current_price
            
            # Place market order
            self.placeOrder(orderId=self.order_id, 
                            contract=self.contract, 
                            order=self.order)
            self.order_id += 1
            
            # Update the current positions
            self.current_position = self.new_signal
            
        # If previous position and the current position are the same, do 
        # nothing
        else:
            print('No need to place a new order')
            
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, \
                    permId, parentIt, lastFillPrice, clientId, whyHeld, \
                    mktCapPrice):
        print(f'\nOrder Status - OrderId: {orderId}, Status: {status}, Filled: {filled}, FilledPrice: {avgFillPrice}')

    def execDetails(self, reqId, contract, execution):
        print('\nOrder Executed:', execution.orderId)
            
    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        print('\nDailyPnL:', round(dailyPnL, 2),
              '\nUnrealized:', round(unrealizedPnL, 2),
              '\nRealized:', round(realizedPnL, 2))
    
    def position(self, account, contract, position, avgCost):
        print('\nAccount:', account, 
              '\nContract:', contract.symbol, 
              '\nPos:', position, 
              '\nAvgCost:', round(avgCost, 2))
    
    def positionEnd(self):
        print('\nPositions retrieved')
    
    def close_connections(self):
        '''
        Disconnect application.
        '''

        self.cancelPositions()
        self.cancelPnL(self.pnl_reqid)
        self.disconnect()
        
    # User defined function to generate request ids
    def getReqId(self):
        
        # Increment request id with 1 every time the function is called
        self.request_id += 1
        print('Request Id: {}'.format(self.request_id))
        return self.request_id
    
    # Callback to handle order ids
    def nextValidId(self, orderId):         
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print('NextValidId:', orderId)
        
# -------------------------x-----------------------x---------------------------

# Strategy entrypoint
app = Strategy()

app.connect(host='localhost', port=7496, clientId=1)

sleep(1)

print('Is application connected to TWS:', app.isConnected())

if app.isConnected() == False:
    
    print('Not able to connect to IB TWS')
    sys.exit()
    
Thread(target=app.run, daemon=True).start()    

# -------------------------x-----------------------x---------------------------

# Define all parameters here

# Define account code
app.account_code = 'DU5017537'

# Below are the strategy run timings
app.start_time = '20220406 09:15:00'
app.end_time = '20220406 23:30:00'

# Date and time format used across strategy
app.tf = tf = '%Y%m%d  %H:%M:%S'

# Strategy parameters
app.ma_period = 20
app.std_num = 1.5
app.is_intraday = True

# Strategy lookback and trading frequency
if app.is_intraday:
    # Determines duration string
    app.lookback_period = str((app.ma_period + 1) * 60) + ' S'
else:
    app.lookback_period = str(app.ma_period + 1) + ' D'

# The following parameters should be in sync with each other
app.trading_frequency = '1 min' # Determines bar size
app.timestamps_frequency = '1T' # Follows strftime format
app.resampling_frequency = 1

# Asset to trade
app.trading_symbol = 'EUR'
app.trading_secType = 'CASH'
app.trading_symbol_currency = 'USD'
app.trading_symbol_exchange = 'IDEALPRO'
# app.trading_symbol_primary_exchange = 'NSE'

# Basic order parameters
app.order_type = 'MKT'
app.order_qty = 20000

# -------------------------x-----------------------x---------------------------

# Build contract object
app.contract = Contract()
app.contract.symbol = app.trading_symbol
app.contract.secType = app.trading_secType
app.contract.currency = app.trading_symbol_currency
app.contract.exchange = app.trading_symbol_exchange
# app.contract.primaryExchange = app.trading_symbol_primary_exchange


# Build order object
app.order = Order()
app.order.action = ''
app.order.totalQuantity = app.order_qty
app.order.orderType = app.order_type

# -------------------------x-----------------------x---------------------------

# Fetch historical data
print('Fetching historical data.')
app.reqHistoricalData(app.getReqId(), 
                      app.contract, 
                      endDateTime='', 
                      durationStr=app.lookback_period, 
                      barSizeSetting=app.trading_frequency, 
                      whatToShow='MIDPOINT', 
                      useRTH=0, 
                      formatDate=1, 
                      keepUpToDate=False, 
                      chartOptions=[])

# Wait for historical data to get downloaded
sleep(2)

# To do: Create an Sqlite database to handle the tick data
app.reqMktData(app.getReqId(), 
               app.contract, 
               genericTickList='', 
               snapshot=False, 
               regulatorySnapshot=False, 
               mktDataOptions=[])

# Fetch last order id
app.order_id = app.nextValidOrderId

def run_strategy():

    app.resample_data()
    
    app.compute_indicators()
    
    app.generate_signals()
    
    app.place_order()
    
# Subscribe to position updates
app.reqPositions()
   
# Subscribe for the PnL updates
app.pnl_reqid = app.getReqId()
app.reqPnL(app.pnl_reqid, app.account_code, "")

# -------------------------x-----------------------x---------------------------

# Generate timestamps
timestamps = pd.date_range(start=app.start_time, 
                           end=app.end_time, 
                           freq=app.timestamps_frequency).strftime(app.tf)

#  Run infinite loop that iterates over the timestamps generated above
try:
    while True:
        
        # Get current time
        app.current_time = dt.now().strftime(app.tf)
        
        # If the current time is less than the strategy start time, then wait
        if dt.strptime(app.current_time, app.tf) < dt.strptime(app.start_time, app.tf):
            print('Wait', app.current_time)
            sleep(1)
            continue
        
        # If the current time is within strategy run time, execute the algorithm
        elif app.current_time in timestamps:
            print('*' * 20)
            print('Executing algorithm:', app.current_time)
            run_strategy()
            
        # If the current time is greater than the strategy run time, then exit the execution
        elif dt.strptime(app.current_time, app.tf) > dt.strptime(app.end_time, app.tf):
            print('Finish. Disconnecting the application:', app.current_time)
            app.disconnect()
            break
        
        sleep(1)
except Exception as e:
    print(traceback.print_exc())
finally:
    app.close_connections()
    print('App disconnected.')