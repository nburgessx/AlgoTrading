# -*- coding: utf-8 -*-
"""
All rights reserved.
@author: IBridgePy@gmail.com
"""
from IBridgePy.constants import DataProviderName, BrokerClientName


class DataProvider(object):
    """
    DataProvider supports both of backtesting or getting real time / hist from 3rd party data provider in real time
    """
    def __init__(self, userConfig, log, useColumnNameWhenSimulatedByDailyBar='close'):
        """
        :param log:
        """
        self._userConfig = userConfig
        # these are needed to construct an instance
        self._log = log

        # The format of self.hist should be self.hist[str_security][barSize] = pandas.df
        # pandas.df index must be int, epoch seconds, columns = open, high, low, close, volume
        # str_security should not have exchange and primaryExchange so that local brokerService does not need to
        # get exchange and primaryExchange
        self._hist = {}

        # a label if the hist has been ingested for backtesting.
        self._histIngested = False

        self._useColumnNameWhenSimulatedByDailyBar = useColumnNameWhenSimulatedByDailyBar

    @property
    def _dataProviderClient(self):
        # The name of the brokerClient of the dataProvider should be the same as the name of the dataProvider.
        if self.name in [DataProviderName.IB, DataProviderName.TD]:
            return self._userConfig.brokerClientFactory.get_brokerClient_by_name(self.name, self._userConfig)
        else:
            return self._userConfig.brokerClientFactory.get_brokerClient_by_name(BrokerClientName.LOCAL, self._userConfig)

    def __str__(self):
        if self._dataProviderClient:
            return '{name=%s dataProviderClient=%s}' % (self.name, self._dataProviderClient)
        else:
            return '{name=%s dataProviderClient=None}' % (self.name,)

    @property
    def name(self):
        """
        Name of the data provider

        :return: string name
        """
        raise NotImplementedError()

    def get_dataProviderClient(self):
        return self._dataProviderClient

    def get_local_variable_hist(self):
        """
        Should be used for testing only
        :return: self._hist
        """
        return self._hist

    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        raise NotImplementedError

    # !!! the returned price will only be used for backtester.!!!
    def provide_real_time_price_from_local_variable_hist(self, security, timeNow, tickType):
        self._log.notset(__name__ + '::provide_real_time_price_from_local_variable_hist: security=%s timeNow=%s tickType=%s' % (security.full_print(), timeNow, tickType))
        if isinstance(tickType, list):
            ans = []
            for ct in tickType:
                ans.append(self._get_one_real_time_price_from_local_variable_hist(security, timeNow, ct))
            return ans
        else:
            return self._get_one_real_time_price_from_local_variable_hist(security, timeNow, tickType)

    def provide_real_time_price(self, security, tickType):
        raise NotImplementedError(self.name)

    def provide_hist_from_a_true_dataProvider(self, security, endTime, goBack, barSize, whatToShow, useRTH):
        raise NotImplementedError(self.name)

    def _get_one_real_time_price_from_local_variable_hist(self, security, timeNow, tickType):
        """
        :param security:
        :param timeNow:
        :param tickType: string ONLY
        :return:
        """
        raise NotImplementedError(self.name)

    # !!! the returned hist will only be used for backtester.!!!
    def provide_historical_data_from_local_variable_hist(self, security, endTime, goBack, barSize, whatToShow, useRTH):
        """

        :param security: IBridgePy::quantopian::Security
        :param endTime: request's ending time with format yyyyMMdd HH:mm:ss {TMZ} ---from IB api doc
        :param goBack:
        :param barSize: string 1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins,
                                30 mins, 1 hour, 1 day
        :param whatToShow:
        :param useRTH:
        :return:
        """
        raise NotImplementedError
