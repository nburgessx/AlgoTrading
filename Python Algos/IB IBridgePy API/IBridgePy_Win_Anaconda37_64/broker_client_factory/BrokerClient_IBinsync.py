#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
There is a risk of loss when trading stocks, futures, forex, options and other
financial instruments. Please trade with capital you can afford to
lose. Past performance is not necessarily indicative of future results.
Nothing in this computer program/code is intended to be a recommendation, explicitly or implicitly, and/or
solicitation to buy or sell any stocks or futures or options or any securities/financial instruments.
All information and computer programs provided here is for education and
entertainment purpose only; accuracy and thoroughness cannot be guaranteed.
Readers/users are solely responsible for how to use these information and
are solely responsible any consequences of using these information.

If you have any questions, please send email to IBridgePy@gmail.com
All rights reserved.
"""
import time
import json

from IBridgePy.constants import BrokerClientName
from broker_client_factory.BrokerClient_IB import ClientIB


# noinspection PyAbstractClass
class IBinsync(ClientIB):
    # !!!
    # DO NOT implement __init___ here. It will override IBCpp.__init__ and cause many errors

    @property
    def name(self):
        return BrokerClientName.IBinsync

    def _check_connectivity_reconn_if_needed(self):
        if not self.isConnectedWrapper():
            time.sleep(0.5)  # TWS needs a little bit time to clean up the previous connection. If no sleep here, errorCode 326 Unable to connect as the client id is already in use. Retry with a unique client id.
            self.connectWrapper()

    def reqPositionsWrapper(self):
        self._check_connectivity_reconn_if_needed()
        self.req_positions()

    def reqCurrentTimeWrapper(self):
        self._check_connectivity_reconn_if_needed()
        self.req_current_time()

    def reqAllOpenOrdersWrapper(self):
        self._check_connectivity_reconn_if_needed()
        self.req_all_open_orders()

    def reqOneOrderWrapper(self, ibpyOrderId):
        # This is not an IB native method. It is customized for Web Api based brokers. IBinsync works as same as Web Api broker
        # so that this method is needed. Invoke reqAllOpenOrdersWrapper() instead of reqOneOrder for IBinsync
        self.reqAllOpenOrdersWrapper()

    def reqAccountUpdatesWrapper(self, subscribe, accountCode):
        self._check_connectivity_reconn_if_needed()
        self.req_account_updates(subscribe, accountCode)

    def reqAccountSummaryWrapper(self, reqId, group, tag):
        self._check_connectivity_reconn_if_needed()
        self.req_account_summary(reqId, group, tag)

    def reqHistoricalDataWrapper(self, reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        # print(__name__ + '::reqHistoricalDataWrapper', endTime, goBack, barSize, whatToShow, useRTH, formatDate)
        self._check_connectivity_reconn_if_needed()
        self.req_historical_data(reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate, False, '')

    def reqMktDataWrapper(self, reqId, contract, genericTickList, snapshot, regulatorySnaphsot=False, mktDataOptions=''):
        self._check_connectivity_reconn_if_needed()
        self.req_mkt_data(reqId, contract, genericTickList, snapshot, regulatorySnaphsot, mktDataOptions)

    def cancelMktDataWrapper(self, reqId):
        self._check_connectivity_reconn_if_needed()
        self.cancel_mkt_data(reqId)

    def reqRealTimeBarsWrapper(self, reqId, contract, barSize, whatToShow, useRTH):
        self._check_connectivity_reconn_if_needed()
        self.req_real_time_bars(reqId, contract, barSize, whatToShow, useRTH)

    def modifyOrderWrapper(self, contract, order, ibpyRequest):
        self._check_connectivity_reconn_if_needed()
        self.placeOrderWrapper(contract, order, ibpyRequest)

    def placeOrderWrapper(self, contract, ibcppOrder, ibpyRequest):
        self._check_connectivity_reconn_if_needed()
        orderId = ibcppOrder.orderId
        if isinstance(orderId, int) and orderId != 0:
            self._log.debug(__name__ + '::placeOrderWrapper: orderId=%s' % (ibcppOrder.orderId,))
            int_orderId = ibcppOrder.orderId
        else:
            int_orderId = self.use_next_id()
            ibcppOrder.orderId = int_orderId
            self._log.debug(__name__ + '::placeOrderWrapper: reqIds and then orderId=%s' % (int_orderId,))
        self._placeOrderHelper(int_orderId, ibpyRequest, contract, ibcppOrder)

    def reqContractDetailsWrapper(self, reqId, contract):
        self._check_connectivity_reconn_if_needed()
        self.req_contract_details(reqId, contract)

    def calculateImpliedVolatilityWrapper(self, reqId, contract, optionPrice, underPrice):
        self._check_connectivity_reconn_if_needed()
        self.calculate_implied_volatility(reqId, contract, optionPrice, underPrice)

    def reqScannerSubscriptionWrapper(self, reqId, subscription):
        self._check_connectivity_reconn_if_needed()
        self.req_scanner_subscription(reqId, json.dumps(subscription), '', '')

    def cancelScannerSubscriptionWrapper(self, tickerId):
        self._check_connectivity_reconn_if_needed()
        self.cancel_scanner_subscription(tickerId)

    def cancelOrderWrapper(self, ibpyOrderId):
        self._check_connectivity_reconn_if_needed()
        ibOrderId = self._idConverter.fromBrokerToIB(ibpyOrderId)
        self._log.info('cancelOrder is sent to %s ibpyOrderId=%s' % (self.name, ibpyOrderId))
        self.cancel_order(ibOrderId)

    def reqScannerParametersWrapper(self):
        self._check_connectivity_reconn_if_needed()
        self.req_scanner_parameters()
