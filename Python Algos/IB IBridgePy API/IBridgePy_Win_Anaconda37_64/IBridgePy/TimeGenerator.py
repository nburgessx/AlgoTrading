# coding=utf-8
import pytz
import datetime as dt

from BasicPyLib.Printable import PrintableII
from IBridgePy.constants import TimeGeneratorType
import pandas as pd
from sys import exit
import time
from BasicPyLib.BasicTools import epoch_to_dt


def make_custom_time_generator(customSpotTimeList):
    for spotTime in customSpotTimeList:
        # pd.Timestamp extends dt.datetime. Therefore, it is acceptable that customSpotTimeList contains pd.Timestamp
        # because ibridgepy time system is coded to handle dt.datetime.
        if not isinstance(spotTime, dt.datetime):
            print(__name__ + '::make_custom_time_generator: spotTime=%s must be a datetime' % (spotTime,))
            exit()
        if spotTime.tzinfo is None:
            print(__name__ + '::make_custom_time_generator: spotTime=%s must have timezone' % (spotTime,))
            exit()
        yield spotTime


def make_auto_time_generator(startingTime, endingTime, freq='1T'):
    """

    :param startingTime:
    :param endingTime:
    :param freq:
    # 1S = 1 second; 1T = 1 minute; 1H = 1 hour; 1D = 1 day
    # https://pandas.pydata.org/pandas-docs/stable/timeseries.html#timeseries-offset-aliases
    :return: a datetime with timezone
    """
    adjustedStartTime = None
    adjustedEndTime = None
    if freq in ['1T']:
        # print('Set second=0 because freq=%s' % (freq,))
        adjustedStartTime = startingTime.replace(second=0)
        adjustedEndTime = endingTime.replace(second=0)
    elif freq in ['1H']:
        # print('Set second=0 minute=0 because freq=%s' % (freq,))
        adjustedStartTime = startingTime.replace(second=0, minute=0)
        adjustedEndTime = endingTime.replace(second=0, minute=0)
    elif freq in ['1D']:
        # print('Set second=0 minute=0 hour=0 because freq=%s' % (freq,))
        adjustedStartTime = startingTime.replace(second=0, minute=0, hour=0)
        adjustedEndTime = endingTime.replace(second=0, minute=0, hour=0)
    elif freq in ['1S']:
        adjustedStartTime = startingTime
        adjustedEndTime = endingTime
    else:
        exit(__name__ + '::make_auto_time_generator: Exit, cannot handle freq=%s' % (freq,))
    tmp = pd.date_range(adjustedStartTime, adjustedEndTime, freq=freq, tz=pytz.timezone('US/Eastern'))

    # The 1st time point will be used by broker_client::CallBacks::currentTime so that handle_data will miss 1st time point.
    # The solution is to repeat 1st time point once to compensate
    tmp = [tmp[0]] + list(tmp)
    for ct in tmp:
        yield ct.to_pydatetime()


def make_local_time_generator():
    """

    :return: a datetime with timezone
    """
    while True:
        # print(__name__ + '::make_local_time_generator: %s' % (time.time(),))
        yield epoch_to_dt(int(time.time()))


class Iter(PrintableII):
    def __init__(self, generator):
        self.generator = generator

    def get_next(self):
        # print(__name__ + '::get_next: self.generator=%s' % (self.generator,))
        return next(self.generator)


class TimeGeneratorFactory(object):
    def __init__(self):
        self._singleton = None

    def get_timeGenerator(self, timeGeneratorConfig):
        if self._singleton:
            return self._singleton
        self._singleton = TimeGenerator(timeGeneratorConfig)
        return self._singleton


class TimeGenerator(PrintableII):
    def __init__(self, timeGeneratorConfig):
        if timeGeneratorConfig.timeGeneratorType == TimeGeneratorType.AUTO:
            self.iter = Iter(make_auto_time_generator(timeGeneratorConfig.startingTime,
                                                      timeGeneratorConfig.endingTime,
                                                      timeGeneratorConfig.freq))
            self._isBacktest = True
        elif timeGeneratorConfig.timeGeneratorType == TimeGeneratorType.LIVE:
            self.iter = Iter(make_local_time_generator())
            self._isBacktest = False
        elif timeGeneratorConfig.timeGeneratorType == TimeGeneratorType.CUSTOM:
            self.iter = Iter(make_custom_time_generator(timeGeneratorConfig.custom))
            self._isBacktest = True

        self._timeNow = None
        self._diffBetweenLocalAndServer = dt.timedelta(0)

    def get_current_time(self):
        """
        This should be used most of the time, except repeater.
        :return: dt.datetime
        """
        if not self._isBacktest:
            return self.iter.get_next()

        if self._timeNow is None:
            self._timeNow = self.iter.get_next()
        # print(__name__ + '::_get_current_time:_timeNow=%s self._diffBetweenLocalAndServer=%s' % (self._timeNow, self._diffBetweenLocalAndServer,))
        # When backtester is using timeGeneratorType = 'CUSTOM' customSpotTimeList = [], user may create a list of spot time
        # by pd.date_range(), which returns a list of pd.Timestamp.
        if isinstance(self._timeNow, pd.Timestamp):
            self._timeNow = self._timeNow.to_pydatetime()
        return self._timeNow + self._diffBetweenLocalAndServer

    def get_next_time(self):
        """
        This should ONLY be used by repeater to advance time, either live or backtest.
        :return: dt.datetime
        """
        # print(__name__ + '::__get_next_time:self._diffBetweenLocalAndServer=%s' % (self._diffBetweenLocalAndServer,))
        self._timeNow = self.iter.get_next()
        return self._timeNow + self._diffBetweenLocalAndServer

    def set_diffBetweenLocalAndServer(self, dt_serverTime):
        # For backtest, there is no need to set diff between local and server because server is local already.
        if self._isBacktest:
            return
        self._diffBetweenLocalAndServer = dt_serverTime - self.iter.get_next()
