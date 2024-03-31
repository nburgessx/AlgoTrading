#
# Simple Tick Data Collector
# zmq Subscriber
#
import zmq
import json
import pandas as pd

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://127.0.0.1:5555')
socket.setsockopt_string(zmq.SUBSCRIBE, '')

ticks = pd.DataFrame()

while True:
    msg = socket.recv_string()
    data = json.loads(msg)
    df = pd.DataFrame({'SYMBOL': data['SYMBOL'], 'PRICE': data['PRICE']},
                      index=[pd.Timestamp(data['TIME'])])
    ticks = pd.concat((ticks, df))
    print(data)
