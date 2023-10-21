"""
Copyright (C) 2019 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
 and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable.
"""
import traceback

"""
Just a thin wrapper around a socket.
It allows us to keep some other info along with it.
"""


import socket
import threading
import logging
from ibapi.errors import FAIL_CREATE_SOCK
from ibapi.errors import CONNECT_FAIL
from ibapi.common import NO_VALID_ID
import time
from sys import exit


#TODO: support SSL !!

logger = logging.getLogger(__name__)


class Connection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.wrapper = None
        self.lock = threading.Lock()
        if not self.host:
            exit(f'{__name__}::connection host=None')
        if not self.port:
            exit(f'{__name__}::connection port=None')

    def connect(self):
        try:
            self.socket = socket.socket()
        #TODO: list the exceptions you want to catch
        except socket.error as err:
            logger.debug(f'connect failed. err={err}')
            if self.wrapper:
                self.wrapper.error(NO_VALID_ID, FAIL_CREATE_SOCK.code(), FAIL_CREATE_SOCK.msg(), '')

        try:
            self.socket.connect((self.host, self.port))
        except socket.error:
            if self.wrapper:
                self.wrapper.error(NO_VALID_ID, CONNECT_FAIL.code(), CONNECT_FAIL.msg(), '')

        self.socket.settimeout(1)   #non-blocking

    def disconnect(self):
        self.lock.acquire()
        try:
            if self.socket is not None:
                logger.debug("disconnecting")
                self.socket.close()
                self.socket = None
                logger.debug("disconnected")
                if self.wrapper:
                    self.wrapper.connectionClosed()
        finally:
            self.lock.release()

    def isConnected(self):
        return self.socket is not None

    def sendMsg(self, msg):
        logger.debug("acquiring lock")
        self.lock.acquire()
        logger.debug("acquired lock")
        if not self.isConnected():
            logger.debug("sendMsg attempted while not connected, releasing lock")
            self.lock.release()
            return 0
        try:
            nSent = self.socket.send(msg)
        except socket.error:
            logger.debug("exception from sendMsg %s", traceback.format_exc())
            nSent = 0
        finally:
            logger.debug("releasing lock")
            self.lock.release()
            logger.debug("release lock")

        logger.debug("sendMsg: sent: %d", nSent)

        return nSent

    def recvMsg(self):
        if not self.isConnected():
            logger.debug("recvMsg attempted while not connected, releasing lock")
            return b""
        try:
            buf = self._recvAllMsg()
            # receiving 0 bytes outside a timeout means the connection is either
            # closed or broken
            if len(buf) == 0:
                pass
                # logger.error("socket either closed or broken, disconnecting")
                # self.disconnect()
                # self._reconnect()
        except socket.timeout:
            logger.debug("socket timeout from recvMsg %s", traceback.format_exc())
            buf = b""
        except socket.error:
            logger.info("socket broken, reconnected")
            # self.disconnect()
            # self._reconnect()
            buf = b""
        except OSError as err:
            # Thrown if the socket was closed (ex: disconnected at end of script) 
            # while waiting for self.socket.recv() to timeout.
            logger.error(f"Socket is broken or closed. err={err}")
            # self._reconnect()
        return buf

    def _reconnect(self):
        time.sleep(3)
        logger.info('Try to reconnect socket')
        self.connect()

    def _recvAllMsg(self):
        cont = True
        allbuf = b""

        while cont and self.isConnected():
            buf = self.socket.recv(4096)
            allbuf += buf
            logger.debug("len %d raw:%s|", len(buf), buf)

            if len(buf) < 4096:
                cont = False

        return allbuf

