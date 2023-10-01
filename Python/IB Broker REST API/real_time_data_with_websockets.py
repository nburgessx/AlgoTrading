# -*- coding: utf-8 -*-
"""
Created on Sun, 1st October 2023

@author: Nicholas Burgess

@documentation link: https://interactivebrokers.github.io/cpwebapi/RealtimeSubscription.html
"""

# 1. Connect to websockets
# 2. Fetch accounts
# 3. Subscribe to market data
# 4. Receive market data
# 5. Parse the market data

import websocket
import requests
import json
import ssl
import warnings
from datetime import datetime

warnings.filterwarnings(action='ignore')

fields = {'fields':['31', '84', '86', '85', '88']}
contract = '12087792'

def on_message(ws, message):
    # print(message)
    
    # Convert message to Python dictionary
    message = json.loads(message)
    
    # Parse data and print it
    desired_topic = 'smd+' + contract
        
    if message['topic'] == desired_topic:
        
        data = ''
        
        t = datetime.fromtimestamp(message['_updated'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        
        if '31' in message.keys():
            last_price = message['31']
            data = data + 'LTP: ' + str(last_price)

        if '84' in message.keys():
            bid = message['84']
            data = data + ' Bid: ' + bid
        
        if '86' in message.keys():
            ask = message['86']
            data = data + ' Ask: ' + ask
        
        if '85' in message.keys():
            ask_size = message['85']
            data = data + ' Ask Size: ' + ask_size
        
        if '88' in message.keys():
            bid_size = message['88']
            data = data + ' Bid Size: ' + bid_size
        
        print(t, data)
    
def on_error(ws, error):
    print(error)
    
def on_close(ws, close_status_code, close_msg):
    print('Connection Closed.')
    
def on_open(ws):
    
    # Fetch accounts
    url = 'https://localhost:5000/v1/api/iserver/accounts'
    response = requests.get(url, headers={}, data={}, verify=False)
    
    # Check for Successful Response
    if response.status_code == 200:
        print('Accounts Fetched.')
        
    # Subscribe to market data
    action = 'smd'
    request = action + '+' + contract + '+' + json.dumps(fields)
    ws.send(request)

if __name__ == '__main__':
    
    # Enable stacktrace
    websocket.enableTrace(True)
    
    # Connect to websockets
    ws = websocket.WebSocketApp('wss://localhost:5000/v1/api/ws',
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    