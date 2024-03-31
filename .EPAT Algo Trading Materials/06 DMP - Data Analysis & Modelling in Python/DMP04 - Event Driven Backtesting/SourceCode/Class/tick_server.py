#
# Simple Tick Data Server
# zmq Publisher
#
import zmq
import json
import time
import random
import datetime

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://127.0.0.1:5555')

AAPL = 100.
MSFT = 100.

while True:
    t = str(datetime.datetime.now())
    if random.random() > 0.5:
        AAPL += random.gauss(0, 1) / 2
        data = {'TIME': t, 'SYMBOL': 'AAPL', 'PRICE': round(AAPL, 2)}
    else:
        MSFT += random.gauss(0, 1) / 2
        data = {'TIME': t, 'SYMBOL': 'MSFT', 'PRICE': round(MSFT, 2)}
    print(data)
    socket.send_string(json.dumps(data))
    time.sleep(random.random() * 2)

