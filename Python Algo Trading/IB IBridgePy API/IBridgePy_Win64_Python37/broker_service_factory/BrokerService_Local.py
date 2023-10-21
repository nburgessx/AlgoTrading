# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""

from BasicPyLib.BasicTools import dt_to_epoch
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.constants import BrokerServiceName, BrokerName
from broker_client_factory.BrokerClientDefs import ReqMktData, PlaceOrder
from broker_service_factory.BrokerService_callback import CallBackType
from sys import exit


# noinspection PyAbstractClass
class LocalBroker(CallBackType):
    def __init__(self, userConfig, log, timeGenerator, singleTrader, dataFromServer, balanceLog):
        self._asDataProviderService = False  # False = backtesting; True = work as a dataProviderService, a dataProvider in brokerClient_Local is responsible to provide data/hist

        # A flag to tell if at least one order is placed in a cycle of handle_data.
        # If yes, need to update NetLiquidation and GrossPositionValue
        self._is_order_placed = False

        self._balanceLog = balanceLog
        super(CallBackType, self).__init__(userConfig, log, timeGenerator, singleTrader, dataFromServer)

    @property
    def name(self):
        return BrokerServiceName.LOCAL_BROKER

    @property
    def brokerName(self):
        return BrokerName.LOCAL

    def get_option_info(self, security, fields, waitForFeedbackInSeconds=30):
        raise NotImplementedError(self.name)

    def _get_account_info_one_tag(self, accountCode, tag, meta='value'):
        if tag not in ['TotalCashValue', 'NetLiquidation', 'GrossPositionValue', 'BuyingPower']:
            self._log.error(__name__ + '::_get_account_info_one_tag: EXIT, cannot handle tag=%s' % (tag,))
            exit()
        ans = 0.0
        if tag in ['TotalCashValue', 'BuyingPower']:
            ans = self._get_TotalCashValue(accountCode)
        elif tag == 'GrossPositionValue':
            ans = self._calculate_grossPositionValue(accountCode)
        elif tag == 'NetLiquidation':
            ans = self._get_TotalCashValue(accountCode) + self._calculate_grossPositionValue(accountCode)
        self._log.debug(__name__ + '::_get_account_info_one_tag: accountCode=%s tag=%s' % (accountCode, tag))
        return ans

    def _calculate_grossPositionValue(self, accountCode):
        allPositions = self.get_all_positions(accountCode)
        self._log.notset(__name__ + f'::_calculate_grossPositionValue: accountCode={accountCode} allPositions={allPositions}')
        ans = 0.0
        for security in allPositions:
            currentPrice = self.get_real_time_price(security, IBCpp.TickType.LAST)
            share = allPositions[security].amount
            ans += currentPrice * float(share)
            self._log.debug(__name__ + '::_calculate_grossPositionValue: security=%s share=%s currentPrice=%s sum=%s' % (security, share, currentPrice, ans))
        self._log.debug(__name__ + '::_calculate_grossPositionValue: accountCode=%s returnedValue=%s' % (accountCode, ans))
        return ans

    def _get_TotalCashValue(self, accountCode):
        ans = self._singleTrader.get_account_info(self.name, accountCode, 'TotalCashValue')
        if ans is None:
            self._log.error(__name__ + '::_get_TotalCashValue: EXIT, no value based on accountCode=%s tag=TotalCashValue' % (accountCode,))
            print('active accountCode is %s' % (self._singleTrader.get_all_active_accountCodes(self.name),))
            print(self._singleTrader)
            exit()
        self._log.debug(__name__ + '::_get_TotalCashValue: accountCode=%s returnedValue=%s' % (accountCode, ans))
        return ans

    def get_real_time_price(self, security, tickType, followUp=True):
        """
        Different from other brokerService because this way is faster for backtesting
        :param followUp:
        :param security:
        :param tickType:
        :return:
        """
        if self._asDataProviderService:
            # This is not backtesting.
            # the 3rd party data provider will provide real time price.
            ans = self._brokerClient.getDataProvider().provide_real_time_price(security, tickType)
        else:
            # self.get_datetime is the current backtesting simulated datetime.
            ans = self._brokerClient.getDataProvider().provide_real_time_price_from_local_variable_hist(security, self.get_datetime(), tickType)
        self._log.debug(__name__ + '::get_real_time_price: security=%s tickType=%s returnedValue=%s' % (security, tickType, ans))
        return ans

    def get_real_time_size(self, security, tickType, followUp=True):
        return self.get_real_time_price(security, tickType)

    def get_timestamp(self, security, tickType):
        self._log.notset(__name__ + '::get_timestamp: security=%s tickType=%s' % (security, tickType))
        # if the request of real time price is not already submitted
        # submit_requests guarantee valid ask_price and valid bid_price
        if not self._brokerClient.is_real_time_price_requested(security):
            self.submit_requests(ReqMktData(security))
        return self._dataFromServer.get_value(security, tickType, 'timestamp')

    def get_datetime(self):
        ans = self._timeGenerator.get_current_time()  # !!! get_current_time instead of get_next_time because backtester should not advance the clock when get_datetime() is invoked.
        self._log.notset(__name__ + '::get_datetime=%s' % (ans,))
        return ans

    def place_order(self, ibridgePyOrder, followUp=True, waitForFeedbackInSeconds=30):
        self._log.debug(__name__ + '::place_order: ibridgePyOrder=%s' % (ibridgePyOrder,))
        contract = ibridgePyOrder.requestedContract
        order = ibridgePyOrder.requestedOrder
        reqIdList = self.submit_requests(PlaceOrder(contract=contract, order=order, followUp=followUp,
                                                    waitForFeedbackInSeconds=waitForFeedbackInSeconds))
        self._is_order_placed = True
        return self._brokerClient.get_submit_requests_result(reqIdList[0])  # return ibpyOrderId

    def processMessages(self, timeNow):
        self._brokerClient.processMessagesWrapper(timeNow)

        # Update account info if any order has been placed.
        if self._is_order_placed:
            accounts = self._singleTrader.get_all_active_accountCodes(self.name)
            self._log.notset(__name__ + f'::processMessages: accounts={accounts}')
            for accountCode in accounts:
                newPositionValue = self._calculate_grossPositionValue(accountCode)
                newPortfolioValue = self._get_TotalCashValue(accountCode) + newPositionValue
                # Only update NetLiquidation and GrossPositionValue, not update TotalCashValue
                # because TotalCashValue has been updated when CallBacks.py::execDetails is invoked.
                self._brokerClient.simulateUpdateAccountValue('NetLiquidation', str(newPortfolioValue), 'USD', accountCode)
                self._brokerClient.simulateUpdateAccountValue('GrossPositionValue', str(newPositionValue), 'USD', accountCode)
                newPortfolioValue = self.get_account_info(accountCode, 'NetLiquidation')
                newCashValue = self.get_account_info(accountCode, 'TotalCashValue')
                self._balanceLog.info(f'{dt_to_epoch(self.get_datetime())} {newPortfolioValue} {newCashValue}', verbose=False)
            self._is_order_placed = False
