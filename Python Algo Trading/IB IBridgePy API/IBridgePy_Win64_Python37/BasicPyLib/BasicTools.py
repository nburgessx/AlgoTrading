# coding=utf-8
import platform
import random
from sys import exit
import pandas as pd
import pytz
import datetime as dt
import sys
import os


class CONSTANTS(object):
    def __init__(self):
        pass

    def get(self, key, caller=None):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            if caller:
                print(__name__, '::CONSTANTS: key=%s does not exist from %s. caller=%s' % (key, self, caller))
            else:
                print(__name__, '::CONSTANTS: key=%s does not exist from %s. caller=None. ' % (key, self))
            exit()


class Timer(object):
    def __init__(self):
        self.startTime = dt.datetime.now()

    def elapsedInSecond(self):
        return (dt.datetime.now() - self.startTime).total_seconds()


def roundToMinTick(price, minTick=0.01):
    """
    for US interactive Brokers, the minimum price change in US stocks is
    $0.01. So if the singleTrader made calculations on any price, the calculated
    price must be round using this function to the minTick, e.g., $0.01
    """
    if price < 0.0:
        exit(f'EXIT, negative price={price}')
    return int(price / minTick) * minTick


def dt_to_epoch(a_dt, showTimeZone=None):
    """
    dt.datetime.fromtimestamp
    the return value depends on local machine timezone!!!!
    So, dt.datetime.fromtimestamp(0) will create different time at different machine
    So, this implementation does not use dt.datetime.fromtimestamp
    """
    # print(__name__ + '::dt_to_epoch: a_dt=%s' % (a_dt,))
    if a_dt.tzinfo is None:
        if showTimeZone:
            a_dt = showTimeZone.localize(a_dt)
        else:
            a_dt = pytz.utc.localize(a_dt)
    return int((a_dt.astimezone(pytz.utc) - pytz.utc.localize(dt.datetime(1970, 1, 1, 0, 0))).total_seconds())


def date_to_epoch(a_date):
    return timestamp_to_epoch(pd.Timestamp(a_date))


def epoch_to_dt(utcInSeconds, str_timezone='UTC'):
    return pytz.timezone(str_timezone).localize(dt.datetime.utcfromtimestamp(int(utcInSeconds)))
    # Another implementation
    # return dt.datetime.utcfromtimestamp(epoch, tz=pytz.utc)


def timestamp_to_epoch(aTimestamp):
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
    if type(aTimestamp) is dt.datetime:
        return dt_to_epoch(aTimestamp)
    if aTimestamp.tzinfo:
        aTimestamp = aTimestamp.astimezone(pytz.utc)
        a = pd.Timestamp(0, tzinfo=pytz.utc)  # epoch zero = Jan 1st 1970
    else:
        a = pd.Timestamp(0)  # epoch zero = Jan 1st 1970
    return (aTimestamp - a) // pd.Timedelta('1s')


def convert_datetime_to_date(aDatetime):
    aDate = None
    if isinstance(aDatetime, dt.datetime):
        aDate = aDatetime.date()
    elif isinstance(aDatetime, dt.date):
        aDate = aDatetime
    else:
        exit(__name__ + '::isTradingDay: EXIT, cannot handle aDatetime=%s' % (aDatetime,))
    return aDate


def isAllLettersCapital(word):
    for letter in word:
        if letter.isalpha():
            if not letter.isupper():
                return False
    return True


def create_random_hist(startTime, endTime, barSize, miniTick):
    """

    :param startTime: dt.datetime
    :param endTime: dt.datetime
    :param barSize: 1S = 1 second; 1T = 1 minute; 1H = 1 hour
    :param miniTick: float, 0.01, 0.05, 0.1, etc.
    :return: pd.DataFrame('open', 'high', 'low', 'close', 'volume'), index = datetime
    """
    # print(__name__ + '::create_random_hist: startTime=%s endTime=%s barSize=%s' % (startTime, endTime, barSize))
    ans = pd.DataFrame()

    # !!!!!!!
    # pd.data_range is a badly designed function because it cannot recognize timezone
    # It always returns time range in local machine timezone
    # !!!!!!!
    index = pd.date_range(startTime, endTime, freq=barSize, tz=pytz.timezone('UTC'))
    for dateTime in index:
        if dateTime.weekday() <= 4:
            openPrice = random.uniform(50, 100)
            closePrice = openPrice * random.uniform(0.95, 1.05)
            highPrice = max(openPrice, closePrice) * random.uniform(1, 1.05)
            lowPrice = max(openPrice, closePrice) * random.uniform(0.95, 1)

            newRow = pd.DataFrame({'open': roundToMinTick(openPrice, miniTick),
                                   'high': roundToMinTick(highPrice, miniTick),
                                   'low': roundToMinTick(lowPrice, miniTick),
                                   'close': roundToMinTick(closePrice, miniTick),
                                   'volume': random.randint(10000, 50000)},
                                  index=[int(dt_to_epoch(dateTime))])
            ans = pd.concat([ans, newRow])
    # print(epoch_to_dt(ans.index[0]))
    # print(epoch_to_dt(ans.index[-1]))
    return ans


def get_system_info():
    pf = platform.system()
    if pf == 'Darwin':
        pf = 'Mac'
    if 'Anaconda' in sys.version or 'anaconda' in sys.version:  # Anaconda Python 27 works this way
        pythonName = 'Anaconda'

    # Anaconda Python 37 works this way
    elif 'Anaconda' in os.path.dirname(sys.executable) or 'anaconda' in os.path.dirname(sys.executable) \
            or 'Miniconda' in os.path.dirname(sys.executable) or 'miniconda' in os.path.dirname(sys.executable):
        pythonName = 'Anaconda'
    else:
        pythonName = 'Python'
    versionName = int(str(sys.version_info.major) + str(sys.version_info.minor))
    return pf, pythonName, versionName
