#
# Simple Tick Data Client
# zmq Subscriber
#
import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://127.0.0.1:5555')
socket.setsockopt_string(zmq.SUBSCRIBE, '')

while True:
    msg = socket.recv_string()
    data = json.loads(msg)
    print(data)
