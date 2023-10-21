# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""

from sys import exit

# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.constants import BrokerServiceName, BrokerName
from broker_client_factory.BrokerClientDefs import ReqMktData, ReqRealTimeBars
from broker_service_factory.BrokerService_callback import CallBackType


def validate_not_equal_none(funName, val, infoTuple):
    if val is None:
        print(funName, infoTuple, 'should not equal to None')
        exit()


class InteractiveBrokers(CallBackType):
    @property
    def name(self):
        return BrokerServiceName.IB

    @property
    def brokerName(self):
        return BrokerName.IB

    def _get_account_info_one_tag(self, accountCode, tag, meta='value'):
        ans = self._singleTrader.get_account_info(self.brokerName, accountCode, tag, meta)
        if ans is None:
            self._log.error(__name__ + '::_get_account_info_one_tag: EXIT, no value based on accountCode=%s tag=%s meta=%s' % (accountCode, tag, meta))
            print('active accountCode is %s' % (self._singleTrader.get_all_active_accountCodes(self.brokerName),))
            exit()
        return ans

    def get_real_time_price(self, security, tickType, followUp=True):  # return real time price
        self._log.notset(__name__ + '::get_real_time_price: security=%s tickType=%s' % (security.full_print(), tickType))

        # if the request of real time price is not already submitted
        # submit_requests guarantee valid ask_price and valid bid_price
        if not self._brokerClient.is_real_time_price_requested(security):
            self.submit_requests(ReqMktData(security, tickTypeClientAsked=tickType, followUp=followUp))

        return self._get_real_time_price_from_dataFromServer(security, tickType)

    def get_timestamp(self, security, tickType):
        self._log.notset(__name__ + '::get_timestamp: security=%s tickType=%s' % (security, tickType))
        # if the request of real time price is not already submitted
        # submit_requests guarantee valid ask_price and valid bid_price
        if not self._brokerClient.is_real_time_price_requested(security):
            self.submit_requests(ReqMktData(security, tickTypeClientAsked=tickType))
        return self._dataFromServer.get_value(security, tickType, 'timestamp')

    def get_real_time_size(self, security, tickType, followUp=True):  # return real time price
        self._log.debug(__name__ + '::get_real_time_size: security=%s tickType=%s' % (security, tickType))

        # if the request of real time price is not already submitted
        # do it right now
        # submit_requests guarantee valid ask_price and valid bid_price
        # DO NOT guarantee valid size
        if not self._brokerClient.is_real_time_price_requested(security):
            self.submit_requests(ReqMktData(security, tickTypeClientAsked=tickType, followUp=followUp))

        return self._get_real_time_size_from_dataFromServer(security, tickType)

    def get_5_second_real_time_bar(self, security, whatToShow='MIDPOINT', followUp=True):
        self._log.notset(f'{__name__}::get_5_second_real_time_bar: security={security} whatToShow={whatToShow}')
        if not self._brokerClient.is_5_second_real_time_bar_requested(security):
            self.submit_requests(ReqRealTimeBars(security, whatToShow=whatToShow, followUp=followUp))

        return self._get_5_second_real_time_bar_from_dataFromServer(security)

    def get_contract_details(self, security, field, waitForFeedbackInSeconds=30):
        self._log.debug(__name__ + '::get_contract_details: security=%s field=%s' % (security, field))
        return self._brokerClient.get_contract_details(security, field, waitForFeedbackInSeconds=waitForFeedbackInSeconds)
