# Import necessary libraries
import traceback
from datetime import datetime as dt
from datetime import timedelta
from time import sleep
import pandas as pd
from threading import Thread
import websocket
import ssl
import warnings
import json
import talib as ta
from pprint import pprint
from base_functions import (auth_status,
                            fetch_accounts,
                            fetch_contract_details,
                            fetch_historical_data,
                            place_orders,
                            tickle)

warnings.filterwarnings(action='ignore')

# Define all strategy parameters

# Below are the strategy execution timings
# They follow 24-hour format
start_time = '20220705 09:15:00'
end_time = '20220705 15:30:00'

# Parameter to keep track whethe the strategy is initialized or not
is_strategy_initialized = False

# The following parameters should be in sync with each other
trading_frequency = '1 min'
timestamps_frequency = '1T' # Follows strftime format
resampling_frequency = 1

# Define parameters for historical data
bar_size = '1min'
lookback_period = '15min'

# Define RSI parameters
rsi_lookback = 14
rsi_upper = 70
rsi_lower = 30

# Define contract (To Do)
# contract_id = '173418084'
# contract_id = '44652015'
contract_id = '56987333'
exchange = 'NSE'

# Account id - leave it blank
account_id = ''

# Define order parameters (To Do)
order_action = ''
order_quantity = 1
order_type = 'MKT'
order_price = 0

# Define parameters to control print statements
print_pnl = False

# -------------------------x-----------------------x---------------------------

# Define a variable to track current position
current_position = 0

# Define a flag to track whether a new trading signal is generated or not
new_trading_signal = 0

# Define websocket url
ws_url = 'wss://localhost:5000/v1/api/ws'

# Define unicodes for checkmark and cross to be printed on console
# Used only for cosmetics
cross_mark = '\u2A2F'
check_mark = '\u2713'

# Date and time format used across strategy
tf = '%Y%m%d %H:%M:%S'
time_zone = 'Asia/Kolkata'

# -------------------------x-----------------------x---------------------------

ws = None
new_thread = None
hist_data = None
tick_data = pd.DataFrame(columns=['time', 'last_price'])

# -------------------------x-----------------------x---------------------------

# Define fields to stream over websocket
# 31 - Last price

fields = {'fields':['31']}

def on_error(ws, error):
    print(cross_mark + ' Error received on web socket.')
    print('Error:', error)
    
def on_open(ws):
    
    global account_id
    
    print(check_mark + ' Websocket connection established.')
    
    # Fetch accounts
    print('\n--> Fetching the user account.')
    status, account_id = fetch_accounts()
    
    if status:
        
        # Subscribe to market data
        print('\n--> Subscribing to market data.')
        s_action = 'smd'
        s_request = s_action + '+' + contract_id + '+' + json.dumps(fields)
        ws.send(s_request)
        print(check_mark + ' Subscribed to market data.')
        
        # Subscribe to pnl updates
        print('\n--> Subscribing to pnl updates.')
        ws.send('spl+{}')
        print(check_mark + ' Subscribed to pnl updates.')
        
        # Subscribe to order updates
        print('\n--> Subscribing to live order updates.')
        ws.send('sor+{}')
        print(check_mark + ' Subscribed to live order updates.')
        
def on_close(ws, close_status_code, close_msg):
    print(check_mark + ' Web socket connection closed.')
    
def on_message(ws, message):
    
    global tick_data, account_id
    
    # Convert receive data package to Python dictionary
    message = json.loads(message)
    
    desired_topic = 'smd+' + contract_id
    
    if message['topic'] == desired_topic:
        
        data = ''
        
        # Parse the timestamp received from server to human readable format
        t = dt.fromtimestamp(message['_updated'] / 1000).strftime(tf)
        
        if '31' in message.keys():
            last_price = message['31']
            data = data + 'LTP: ' + str(last_price)
            
            new_data = {'time': t,
                        'last_price': last_price}
            
            tick_data = tick_data.append(new_data, ignore_index=True)
            
            # print(t, data)
    
    # Handle pnl updates
    if message['topic'] == 'spl':
        
        if print_pnl:
            pnl_dict = message['args'][account_id + '.Core']
        
            if 'dpl' in pnl_dict:
                print('\nDaily PnL:', pnl_dict['dpl'])
            
            if 'upl' in pnl_dict:
                print('Unrealized PnL:', pnl_dict['upl'])
        
    # Handle live order updates
    if message['topic'] == 'sor':
        
        # Based on order status, current positions should be updated here
        
        pprint(message['args'])

# -------------------------x-----------------------x---------------------------

# Define a function to initialize one time tasks

def initialize_strategy():

    global ws, new_thread, hist_data, account_id
    
    # Check if the strategy is connected or not
    print('\n--> Checking authentication status.')
    auth_status()
    # TODO: What if strategy is not connected?
    
    # Validate contract id
    print('\n--> Fetching contract details.')
    fetch_contract_details(contract_id)
    
    # Fetch historical data
    print('\n--> Fetching historical data.')
    hist_data = fetch_historical_data(contract_id, 
                                      exchange, 
                                      lookback_period,
                                      bar_size,
                                      time_zone)
    
    # Connect to websockets to stream data
    # Enable stacktrace
    websocket.enableTrace(False)
    
    # Connect to websocket
    ws = websocket.WebSocketApp(ws_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    # Start websocket connection on a child thread
    print('\n--> Starting a websocket connection to stream live data.')
    new_thread = Thread(target=ws.run_forever,
                    kwargs={"sslopt":{"cert_reqs": ssl.CERT_NONE}},
                    daemon=True)
    new_thread.start()


def resample_data(current_time):
    
    global tick_data, hist_data
    
    # Determine the previous timestamp from which ticks needs to be resampled
    previous_timestamp = dt.strptime(current_time, tf) - timedelta(minutes=resampling_frequency)
    previous_timestamp = previous_timestamp.strftime(tf)
    
    tick_data['time'] = pd.to_datetime(tick_data['time'])
    
    # Filter data from the tick dataframe to build the current bar
    temp_data = tick_data[(tick_data['time'] > previous_timestamp) & (tick_data['time'] < current_time)]
    
    # Convert index to datetime index and drop time column
    temp_data.set_index(temp_data['time'], inplace=True)
    temp_data.index = pd.to_datetime(temp_data.index)
    temp_data.drop(columns=['time'], inplace=True)
    
    print('Length of tick data:', str(len(temp_data)))
    
    # Build current bar using the tick data
    new_bar = {}
    new_bar['o'] = temp_data.resample(timestamps_frequency).agg('first').iloc[-1, 0]
    new_bar['h'] = temp_data.resample(timestamps_frequency).agg('max').iloc[-1, 0]
    new_bar['l'] = temp_data.resample(timestamps_frequency).agg('min').iloc[-1, 0]
    new_bar['c'] = temp_data.resample(timestamps_frequency).agg('last').iloc[-1, 0]
    new_bar['v'] = 0

    # Create a temporary dataframe to hold a new bar    
    resampled_data = pd.DataFrame(new_bar, index=[current_time])
        
    # Append the new bar to the existing data
    hist_data = hist_data.append(resampled_data)
    
    # print(hist_data.tail(10))

def compute_indicators():
    
    global hist_data
    
    hist_data['rsi_values'] = ta.RSI(hist_data['c'], 
                                     timeperiod=rsi_lookback)
    
    # print(hist_data.tail(10))

def generate_trading_signals():
    
    global hist_data, new_trading_signal, current_position
    
    # Extract current rsi value
    current_rsi_value = hist_data['rsi_values'].iloc[-1]
    
    print('--> Current RSI value:', round(current_rsi_value, 2))
    
    print('--> Current position:', current_position)
    
    # If we don't have any position, check for a new position
    if current_position == 0:
        
        # Check for a new long position
        if current_rsi_value < rsi_lower:
            new_trading_signal = 1
            print('--> New long entry signal got generated.')
        
        elif current_rsi_value > rsi_upper:
            new_trading_signal = -1
            print('--> New short entry signal got generated.')
            
        else:
            print('--> No trading signal.')
            
    elif current_position == 1:
        
        if current_rsi_value > rsi_upper:
            new_trading_signal = 0
            print('--> New long exit signal got generated.')
        
        else:
            print('--> No trading signal.')
            
    elif current_position == -1:
        
        if current_rsi_value < rsi_lower:
            new_trading_signal = 0
            print('--> New short exit signal got generated.')
            
        else:
            print('--> No trading signal.')
            

def execute_orders():
    
    global order_action, account_id, contract_id, order_type, order_quantity
    global order_price, current_position
    
    if current_position != new_trading_signal:
        
        # Close existing positions
        if new_trading_signal == 0:
            
            if current_position == 1:
                order_action == 'SELL'
            
            if current_position == -1:
                order_action == 'BUY'
            
            current_position = 0
        
        elif new_trading_signal == 1:
            order_action = 'BUY'
            current_position = 1
        
        elif new_trading_signal == -1:
            order_action = 'SELL'
            current_position = -1
            
        place_orders(account_id,
                     int(contract_id),
                     order_type,
                     order_action,
                     order_quantity)
        
        print(check_mark + ' Order placed.')

# Define a function to execute strategy
def strategy(current_time):
    
    # Check if the strategy is connected or not
    resample_data(current_time)
    
    compute_indicators()
    
    generate_trading_signals()
    
    execute_orders()
    
    print(check_mark + ' Strategy executed!')
    
# -------------------------x-----------------------x---------------------------

# Generate timestamps
timestamps = pd.date_range(start=start_time, 
                           end=end_time, 
                           freq=timestamps_frequency).strftime(tf)

# Run infinite loop that iterates ovee the timestamps generated above
try:
    while True:

        # Get current time
        current_time = dt.now().strftime(tf)

        # If the current time is earlier than the strategy start time, 
        # then wait.
        if dt.strptime(current_time, tf) < dt.strptime(start_time, tf):
            print('Wait', current_time)
            sleep(1)
            continue

        # If the current time is within the strategy execution time, 
        # then execute the strategy
        elif current_time in timestamps:
            
            if is_strategy_initialized == False:
                initialize_strategy()
                is_strategy_initialized = True
            
            if is_strategy_initialized == True:
                print('\n--> Executing strategy:', current_time)
                strategy(current_time)
        
        # If we don't send any request to server, it will be timed out.
        # To keep the connection with server alive, we tickle it periodically.
        elif dt.strptime(current_time, tf).second == 30:
            # To do: Tickle server 
            if is_strategy_initialized:
                print('\n--> Tickling the local server.')
                tickle()
        
        # If the current time is afterwards the strategy end time, 
        # then stop the strategy.
        elif dt.strptime(current_time, tf) > dt.strptime(end_time, tf):
            if is_strategy_initialized:
                print('\n--> Finish. Logging out.')
                # To Do: Use logout function
            else:
                print('\n' + cross_mark + ' Strategy did not run.')
                print('INFO: Please check strategy run timings.')
                
            break
        else:
            if is_strategy_initialized == False:
                initialize_strategy()
                is_strategy_initialized = True

        sleep(1)
        
except:
    print(traceback.print_exc())
finally:
    # To Do: Include any dicsonnections
    if is_strategy_initialized:
        
        print('\n--> Unsubscribing to market data.')
        ws.send('umd+' + contract_id + '+{}')
        
        print('\n--> Unsubscribing to pnl updates.')
        ws.send('upl+{}')
        
        print('\n--> Unsubscribing to live order updates.')
        ws.send('uor+{}')
        
        print('\n--> Closing a web socket connection.')
        ws.close()
        
        if new_thread.isAlive():
            new_thread.join()
    
        print(check_mark + ' Strategy disconnected.')