# -*- coding: utf-8 -*-
"""
All rights reserved.
@author: IBridgePy@gmail.com
"""

import pytz

from BasicPyLib.BasicTools import dt_to_epoch
from IBridgePy.constants import DataProviderName
from broker_client_factory.CustomErrors import NotEnoughHist
from broker_client_factory.IBridgePy_portal.candle_daily_get import CandleDailyGetClient
from broker_client_factory.IBridgePy_portal.simulate_spot_by_daily import SimulateSpotByDailyGetClient
from .data_provider_nonRandom import NonRandom
import datetime as dt


class IBridgePy(NonRandom):
    def __init__(self, userConfig, log, apiKey, useColumnNameWhenSimulatedByDailyBar):
        self._log = log
        if apiKey:
            self._simulateSpotByDailyGetClient = SimulateSpotByDailyGetClient(apiKey=apiKey, log=self._log)
            self._candleDailyGetClient = CandleDailyGetClient(apiKey=apiKey, log=self._log)
        else:
            exit(__name__ + '::__init__: EXIT, please update the apiKey in settings.py -> EMAIL_CLIENT -> IBRIDGEPY_EMAIL_CLIENT')
        super().__init__(userConfig, log, useColumnNameWhenSimulatedByDailyBar)

    @property
    def name(self):
        return DataProviderName.IBRIDGEPY

    def provide_real_time_price(self, security, tickType):
        # Need to think about how to use this method
        raise NotImplementedError(self.name)

    def provide_hist_from_a_true_dataProvider(self, security, endTime, goBack, barSize, whatToShow, useRTH):
        count, unit = goBack.split(' ')
        if unit == 'D':
            goBack = int(count)
        else:
            exit(__name__ + '::provide_hist_from_a_true_dataProvider: EXIT, cannot handle goBack=%s. Only handle goBack="xx D" right now.' % (goBack,))
        if type(endTime) is str:
            endTime = dt.datetime.strptime(endTime, "%Y%m%d %H:%M:%S %Z")  # string -> dt.datetime
            endTime = pytz.timezone('UTC').localize(endTime)
        epoch = dt_to_epoch(endTime)
        ans = self._candleDailyGetClient.get_candle_daily(ticker=security.symbol, epochSecond=epoch, goBack=goBack)
        return ans

    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        self._ingest_hists(histIngestionPlan, self._get_hist_from_IBPY)
        self._histIngested = True

    # dataProviderClient will be provided by MarketManagerBase::setup_service.
    def _get_hist_from_IBPY(self, plan):
        self._log.debug(__name__ + '::_get_hist_from_IBPY')
        endTime = plan.endTime.astimezone(pytz.timezone('UTC'))
        epoch = dt_to_epoch(endTime)
        goBack = None

        count, unit = plan.goBack.split(' ')
        if unit == 'D':
            goBack = int(count)
        else:
            exit(__name__ + '::_get_hist_from_IBPY: EXIT, cannot handle goBack=%s. Only handle goBack="xx D" right now.' % (plan.goBack,))

        if plan.barSize != '1 day':
            exit(__name__ + '::_get_hist_from_IBPY: EXIT, cannot handle barSize=%s. Only handle barSize="1 day" right now.' % (plan.barSize,))

        ans = self._candleDailyGetClient.get_candle_daily(ticker=plan.security.symbol, epochSecond=epoch, goBack=goBack)
        if not len(ans):
            self._log.error(__name__ + '::_get_hist_from_IBPY: No historical data available at IBridgePy-portal for ticker=%s' % (plan.security.symbol,))
            raise NotEnoughHist()
        return ans

    # DO NOT DELETE !!! Need to consider how to handle it.
    # def _get_one_real_time_price_from_local_variable_hist(self, security, timeNow, tickType, freq='1 min'):
    #     self._log.notset(__name__ + '::_get_one_real_time_price_from_local_variable_hist: security=%s timeNow=%s tickType=%s' % (security.full_print(), timeNow, tickType))
    #     return self._simulateSpotByDailyGetClient.get_spot_price(security.symbol, dt_to_epoch(timeNow), tickType)
