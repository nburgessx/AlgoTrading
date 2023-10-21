# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""
from IBridgePy.constants import DataProviderName
from data_provider_factory.data_provider import DataProvider
from BasicPyLib.BasicTools import roundToMinTick, create_random_hist
from IBridgePy.IbridgepyTools import stripe_exchange_primaryExchange_from_security, calculate_startTime
import random
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from sys import exit


def barSizeTransformer(barSize):
    transfer = {'1 second': '1S',
                '1 minute': '1T',
                '1 min': '1T',
                '15 mins': '15T',
                '1 hour': '1H',
                '4 hours': '4H',
                '1 day': '1D'}
    ans = transfer.get(barSize)
    if ans:
        return ans
    else:
        exit(__name__ + '::barSizeTransformer: EXIT, cannot handle barSize=%s' % (barSize,))


class RandomDataProvider(DataProvider):
    # Used as a cache to speed up
    _lastRealTimePrice = {}

    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        self._histIngested = True

    @property
    def name(self):
        return DataProviderName.RANDOM

    def _get_one_real_time_price_from_local_variable_hist(self, security, timeNow, tickType):
        # print(__name__, '_get_one_real_time_price_from_local_variable_hist', security, timeNow, tickType)
        # Store the last value, be prepared that this function is fired twice at one timeNow
        security_no_exchange_primaryExchange = stripe_exchange_primaryExchange_from_security(security)
        str_security = security_no_exchange_primaryExchange.full_print()
        if (str_security, timeNow, tickType) in self._lastRealTimePrice:
            self._log.notset(__name__ + '::_get_one_real_time_price_from_local_variable_hist: str_security=%s timeNow=%s tickType=%s returnedValue=SavedValue' % (str_security, timeNow, tickType))
            return self._lastRealTimePrice[(str_security, timeNow, tickType)]

        ans = -1
        if tickType in [IBCpp.TickType.ASK, IBCpp.TickType.BID, IBCpp.TickType.LAST, IBCpp.TickType.OPEN,
                        IBCpp.TickType.HIGH, IBCpp.TickType.LOW, IBCpp.TickType.CLOSE]:
            ans = roundToMinTick(random.uniform(50, 100))
        elif tickType in [IBCpp.TickType.VOLUME, IBCpp.TickType.BID_SIZE, IBCpp.TickType.ASK_SIZE]:
            ans = roundToMinTick(random.uniform(10000, 50000), 1)
        else:
            self._log.error(__name__ + '::_get_one_real_time_price_from_local_variable_hist: EXIT, do not support tickType=%s' % (str(tickType),))
            exit()
        self._lastRealTimePrice[(str_security, timeNow, tickType)] = ans
        if tickType == IBCpp.TickType.CLOSE:
            self._lastRealTimePrice[(str_security, timeNow, IBCpp.TickType.ASK)] = ans
            self._lastRealTimePrice[(str_security, timeNow, IBCpp.TickType.BID)] = ans
        self._log.notset(__name__ + '::_get_one_real_time_price_from_local_variable_hist: str_security=%s timeNow=%s tickType=%s returnedValue=%s' % (str_security, timeNow, tickType, ans))
        return ans

    def provide_historical_data_from_local_variable_hist(self, security, endTime, goBack, barSize, whatToShow, useRTH):
        """
        endTime: string with timezone of UTC !!!
        :return: pd.DataFrame('open', 'high', 'low', 'close', 'volume'), index = datetime
        """
        self._log.debug(__name__ + '::get_historical_data: security=%s endTime=%s goBack=%s barSze=%s whatToShow=%s useRTH=%s' % (security.full_print(), endTime, goBack, barSize, whatToShow, useRTH))
        startTime, endTime = calculate_startTime(endTime, goBack, barSize)
        self._log.debug(__name__ + '::get_historical_data: startTime=%s endTime=%s' % (startTime, endTime))
        return create_random_hist(startTime, endTime, barSizeTransformer(barSize), miniTick=0.01)

    def provide_real_time_price(self, security, tickType):
        ans = roundToMinTick(random.uniform(50, 100))
        # print(__name__ + '::provide_real_time_price: ans=%s' % (ans,))
        self._log.notset(__name__ + '::provide_real_time_price: ans=%s' % (ans,))
        return ans

    def provide_hist_from_a_true_dataProvider(self, security, endTime, goBack, barSize, whatToShow, useRTH):
        raise NotImplementedError(self.name)
