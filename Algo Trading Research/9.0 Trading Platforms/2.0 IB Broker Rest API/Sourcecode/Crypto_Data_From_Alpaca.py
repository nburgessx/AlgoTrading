# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 22:07:58 2021

@author: Jay Parmar

@documentation: https://alpaca.markets/docs/api-documentation/api-v2/market-data/alpaca-crypto-data/real-time/
"""

import json
import websocket
import warnings
import ssl

warnings.filterwarnings(action='ignore')

# Read Alpaca Key and Secret
f = open('alpaca_keys.txt', 'r').read().split('\n')
api_key = f[0]
api_secret = f[1]

def on_message(ws, message):
    
    parsed_msg = json.loads(message)
    
    t = parsed_msg[0]['T']
    
    if t == 'success':
        msg = parsed_msg[0]['msg']
        
        if msg == 'connected':
            # Send authentication details
            data_to_send = {'action': 'auth',
                            'key': api_key,
                            'secret': api_secret}
    
            d = json.dumps(data_to_send)
            ws.send(d)
        
        if msg == 'authenticated':
            # Send subscription details
            data_to_send = {'action': 'subscribe',
                            'quotes': ['BTCUSD']}
            
            d = json.dumps(data_to_send)
            ws.send(d)
            
    if t == 'q':
        symbol = parsed_msg[0]['S']
        bid_price = parsed_msg[0]['bp']
        ask_price = parsed_msg[0]['ap']
        time = parsed_msg[0]['t']
        
        print(symbol, time, 'Bid:', bid_price, 'Ask:', ask_price)
    
    
def on_error(ws, error):
    print(error)
    
def on_close(ws, close_status_code, close_msg):
    print('Connection Closed.')
    
def on_open(ws):
    pass
    
if __name__ == '__main__':
    
    # Enable stacktrace
    websocket.enableTrace(True)
    
    ws = websocket.WebSocketApp('wss://stream.data.alpaca.markets/v1beta1/crypto',
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})



