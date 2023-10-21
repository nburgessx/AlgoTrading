# -*- coding: utf-8 -*-
"""
All rights reserved.
@author: IBridgePy@gmail.com
"""
import datetime as dt

import pytz

from IBridgePy.IbridgepyTools import choose_whatToShow
from IBridgePy.constants import DataProviderName
from broker_client_factory.BrokerClientDefs import ReqHistoricalData
from .data_provider_nonRandom import NonRandom


class TD(NonRandom):
    @property
    def name(self):
        return DataProviderName.TD

    def provide_real_time_price(self, security, tickType):
        # Need to think about how to use this method
        raise NotImplementedError(self.name)

    def provide_hist_from_a_true_dataProvider(self, security, endTime, goBack, barSize, whatToShow, useRTH):
        # Need to think about how to use this method
        raise NotImplementedError(self.name)

    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        self._dataProviderClient.connectWrapper()
        self._ingest_hists(histIngestionPlan, self._get_hist_from_TD)
        self._dataProviderClient.disconnectWrapper()
        self._histIngested = True

    # dataProviderClient will be provided by MarketManagerBase::setup_service.
    # The real BrokerClient_TD will be provided to retrieve data from TD.
    def _get_hist_from_TD(self, plan):
        self._log.debug(__name__ + '::_get_hist_from_TD')
        endTime = plan.endTime.astimezone(pytz.timezone('UTC'))
        endTime = dt.datetime.strftime(endTime, "%Y%m%d %H:%M:%S %Z")  # datetime -> string
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
