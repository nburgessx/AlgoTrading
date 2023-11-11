# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""
import datetime as dt

import pytz

from IBridgePy.IbridgepyTools import choose_whatToShow
from IBridgePy.constants import DataProviderName
from broker_client_factory.BrokerClientDefs import ReqHistoricalData
from .data_provider_nonRandom import NonRandom


class IB(NonRandom):
    @property
    def name(self):
        return DataProviderName.IB

    def provide_hist_from_a_true_dataProvider(self, security, str_endTime, goBack, barSize, whatToShow, useRTH):
        self._log.info(f"{__name__}::provide_hist_from_a_true_dataProvider: security={security} str_endTime={str_endTime} goBack={goBack} barSize={barSize} whatToShow={whatToShow} useRTH={useRTH} self._dataProviderClient={self._dataProviderClient}")
        self._dataProviderClient.connectWrapper()
        self._dataProviderClient.add_exchange_to_security(security)
        self._dataProviderClient.add_primaryExchange_to_security(security)
        # IB only accepts str_endTime with a timezone of UTC.
        reqIds = self._dataProviderClient.request_data(ReqHistoricalData(security, barSize, goBack, str_endTime, whatToShow))
        # only reqId is returned
        hist = self._dataProviderClient.get_submit_requests_result(reqIds[0])
        return hist

    def provide_real_time_price(self, security, tickType):
        # Need to think about how to use this method
        raise NotImplementedError(self.name)

    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        # broker_client_factory is responsible to invoke connectWrapper
        self._ingest_hists(histIngestionPlan, self._get_hist_from_IB)
        self._histIngested = True

    # dataProviderClient will be provided by MarketManagerBase::setup_service.
    # The real BrokerClient_IB will be provided to retrieve data from IB.
    def _get_hist_from_IB(self, plan):
        self._log.debug(__name__ + '::_get_hist_from_IB: plan=%s' % (plan,))
        if plan.fileName is not None:
            self._log.error(__name__ + '::_get_hist_from_IB: plan=%s should not have fileName. dataProviderName should be LOCAL_FILE.' % (plan,))
            exit()
        endTime = plan.endTime.astimezone(pytz.timezone('UTC'))
        endTime = dt.datetime.strftime(endTime, "%Y%m%d %H:%M:%S %Z")  # datetime -> string
        self._dataProviderClient.add_exchange_to_security(plan.security)
        self._dataProviderClient.add_primaryExchange_to_security(plan.security)
        # the return of request_data is reqId.
        # To get the content of hist, call brokerService::request_historical_data
        whatToShow = choose_whatToShow(plan.security.secType)
        reqIds = self._dataProviderClient.request_data(ReqHistoricalData(plan.security,
                                                                         plan.barSize,
                                                                         plan.goBack,
                                                                         endTime,
                                                                         whatToShow))

        # only reqId is returned
        hist = self._dataProviderClient.get_submit_requests_result(reqIds[0])
        # hist.to_csv('%s_%s_%s.csv' % (plan.security, plan.barSize, plan.goBack))
        return hist
