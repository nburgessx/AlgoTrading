# -*- coding: utf-8 -*-
"""
Created on Thu Dec 25 19:01:54 2014

@author: IBridgePy
"""
import os
import datetime
import pytz

from BasicPyLib.retrying import retry

Level = {
    'NOTSET': 0,  # show more info
    'DEBUG': 10,
    'INFO': 20,
    'ERROR': 30}  # show less info


class SimpleLogger(object):
    def __init__(self, filename, logLevel, folderPath='default', addTime=True, logInMemory=False, verbose=True):
        """ determine US Eastern time zone depending on EST or EDT """
        if datetime.datetime.now(pytz.timezone('US/Eastern')).tzname() == 'EDT':
            self.USeasternTimeZone = pytz.timezone('Etc/GMT+4')
        elif datetime.datetime.now(pytz.timezone('US/Eastern')).tzname() == 'EST':
            self.USeasternTimeZone = pytz.timezone('Etc/GMT+5')
        else:
            self.USeasternTimeZone = None
        self.addTime = addTime  # True: add local time str in front of the records
        self.filename = filename  # User defined fileName
        self._logLevel = Level[logLevel]  #
        self._log_file = None
        self._logInMemory = logInMemory  # When backtesting, only write messages to memory to save time of opening and closing log every time.
        self._allLogMessagesList = []  # all log messages will be written here and dump to file when backtesting is done. List.append will be faster than str concation.
        self._verbose = verbose
        if folderPath == 'default':
            self.folderPath = os.path.join(os.getcwd(), 'Log')
        else:
            self.folderPath = folderPath
        if not os.path.isdir(self.folderPath):
            os.makedirs(self.folderPath)
            print(__name__ + '::__init__: WARNING, create a folder of "Log" at %s' % (self.folderPath,))

    def __str__(self):
        return '{fileName=%s}' % (self.filename,)

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def _write_to_log(self, msg, verbose=True):
        currentTime = datetime.datetime.now(tz=self.USeasternTimeZone)
        if self._verbose and verbose:
            print(msg)
        if self._logInMemory:
            self._allLogMessagesList.append(msg)
        else:
            self.open_file()
            if self.addTime:
                self._log_file.write(str(currentTime) + ": " + msg + '\n')
            else:
                self._log_file.write(msg + '\n')
            self.close_log()

    def write_all_messages_to_file(self):
        if self._allLogMessagesList:
            self.open_file()
            allLog = '\n'.join(self._allLogMessagesList)
            self._log_file.write(allLog)
            self.close_log()

    def notset(self, msg, verbose=True):
        if self._logLevel <= Level['NOTSET']:
            self._write_to_log(msg, verbose=verbose)

    def debug(self, msg, verbose=True):
        if self._logLevel <= Level['DEBUG']:
            self._write_to_log(msg, verbose=verbose)

    def info(self, msg, verbose=True):
        if self._logLevel <= Level['INFO']:
            self._write_to_log(msg, verbose=verbose)

    def error(self, msg, verbose=True):
        if self._logLevel <= Level['ERROR']:
            self._write_to_log(msg, verbose=verbose)

    def record(self, *arg, **kwrs):
        msg = ''
        for ct in arg:
            msg += str(ct) + ' '
        for ct in kwrs:
            msg += str(kwrs[ct]) + ' '
        self._write_to_log(msg)

    def close_log(self):
        self._log_file.close()

    def open_file(self):
        self._log_file = open(os.path.join(self.folderPath, self.filename), 'a')


if __name__ == '__main__':
    # c=  SimpleLogger('TestLog.txt', 'DEBUG', addTime=False)
    c = SimpleLogger('TestLog.txt', 'INFO')
    c.info('test_me test_me')
    c.info('test_me 1')
    c.info('test_me 2', verbose=False)
    c.info('test_me 3')
    c.info('test_me 4')
    # c.record(a=1, b=2, c=3)
    c.record(1, 2, 3, 'test_me', 1, 'retest', 4, a=4, b=5, c=6)
