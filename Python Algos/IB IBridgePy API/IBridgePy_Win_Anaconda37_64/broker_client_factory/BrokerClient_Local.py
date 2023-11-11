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

import datetime as dt
from sys import exit
from decimal import Decimal
import json

import pytz
import pandas as pd

from BasicPyLib.BasicTools import dt_to_epoch, roundToMinTick
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.constants import OrderStatus, LiveBacktest, BrokerClientName, BrokerName, DataProviderName
from IBridgePy.quantopian import from_contract_to_security
from broker_client_factory.BrokerClientDefs import ReqAttr
from broker_client_factory.CallBacks import CallBacks
from broker_client_factory.CustomErrors import NotEnoughHist, NotEnoughFund
from models.utils import print_IBCpp_contract, print_IBCpp_order, print_IBCpp_execution


class OrderToBeProcessed(object):
    def __init__(self):
        self._activeOrderDict = {}
        self._nonActiveOrderDict = {}
        self._ocaGroups = {}

    def get_active_orderId_list(self):
        return list(self._activeOrderDict.keys())

    def get_by_orderId(self, int_orderId):
        if int_orderId in self._activeOrderDict:
            return self._activeOrderDict[int_orderId]
        elif int_orderId in self._nonActiveOrderDict:
            return self._nonActiveOrderDict[int_orderId]
        else:
            return None, None
            # exit(__name__ + '::OrderToBeProcessed::get_by_orderId: int_orderId=%s does not exist.' % (int_orderId,))

    def get_by_oca_group(self, oca_group):
        if oca_group in self._ocaGroups:
            return self._ocaGroups[oca_group]
        return None

    def add_order(self, int_orderId, ibcpp_contract, ibcpp_order):
        # print(__name__ + '::add_order: int_orderId=%s ibcpp_contract=%s ibcpp_order=%s' % (int_orderId, print_IBCpp_contract(ibcpp_contract), print_IBCpp_order(ibcpp_order)))
        if ibcpp_order.get('parentId', None) in [0, None]:  # parent order of a bracket orders, or just a single order.
            self._activeOrderDict[int_orderId] = (ibcpp_contract, ibcpp_order)
        else:
            self._nonActiveOrderDict[int_orderId] = (ibcpp_contract, ibcpp_order)
        ocaGroup = ibcpp_order.get('ocaGroup', None)
        if ocaGroup:
            if ocaGroup in self._ocaGroups:
                self._ocaGroups[ocaGroup].append(int_orderId)
            else:
                self._ocaGroups[ocaGroup] = [int_orderId]

    def cancel_order(self, int_orderId):
        if int_orderId in self._activeOrderDict:
            ibcpp_contract, ibcpp_order = self._activeOrderDict[int_orderId]
            self._delete_ocaGroup(ibcpp_order.get('ocaGroup', None))
        else:
            ibcpp_contract, ibcpp_order = self._nonActiveOrderDict[int_orderId]
            self._delete_ocaGroup(ibcpp_order.get('ocaGroup', None))

    def fill_order(self, int_orderId):
        # print(__name__ + '::fill_order: int_orderId=%s' % (int_orderId,))
        ibcpp_contract, ibcpp_order = self._activeOrderDict[int_orderId]
        ocaGroup = ibcpp_order.get('ocaGroup', None)
        parentId = ibcpp_order.get('parentId', None)
        if parentId:  # Either stoploss or takeprofit order is filled. Then, delete all related orders
            self._delete_ocaGroup(ocaGroup)
        else:
            if ocaGroup:
                # parent order of a bracket orders is filled, need to convert related orders to active
                # print(self._ocaGroups[ocaGroup])
                self._ocaGroups[ocaGroup].remove(int_orderId)
                self._purely_delete_order_ignoring_ocaGroup(int_orderId)
                for orderId in self._ocaGroups[ocaGroup]:
                    self._move_from_nonActive_to_active(orderId)
            else:
                # a single order is filled, just delete
                self._purely_delete_order_ignoring_ocaGroup(int_orderId)

    def _move_from_nonActive_to_active(self, int_orderId):
        if int_orderId in self._nonActiveOrderDict:
            ibcpp_contract, ibcpp_order = self._nonActiveOrderDict[int_orderId]
            self._activeOrderDict[int_orderId] = (ibcpp_contract, ibcpp_order)
            del self._nonActiveOrderDict[int_orderId]
        else:
            exit(__name__ + '::_move_from_nonActive_to_active: int_orderId=%s is not in self._nonActiveOrderDict' % (int_orderId,))

    def _purely_delete_order_ignoring_ocaGroup(self, int_orderId):
        if int_orderId in self._activeOrderDict:
            del self._activeOrderDict[int_orderId]
        if int_orderId in self._nonActiveOrderDict:
            del self._nonActiveOrderDict[int_orderId]

    def _delete_ocaGroup(self, ocaGroup):
        if not ocaGroup:
            return
        ocaOrders = self._ocaGroups[ocaGroup]
        del self._ocaGroups[ocaGroup]
        for orderId in ocaOrders:
            self._purely_delete_order_ignoring_ocaGroup(orderId)


class ClientLocalBroker(CallBacks):
    # !!!
    # DO NOT implement __init___ here. It will override IBCpp.__init__ and cause many errors
    def setup_this_client(self, userConfig, log, accountCode, rootFolderPath, singleTrader, data, timeGenerator, dataProvider, transactionLog, simulate_commission):
        # Simulate the pending order book on IB server side.
        # keyed by ibpyOrderId, value = (contract, order)
        # Delete records when the order is executed by simulation.
        # noinspection PyAttributeOutsideInit
        self._orderToBeProcessed = OrderToBeProcessed()

        # Clients want to ignore some errors from the broker, instead of terminating the code.
        # It should be a list of error codes, such as [112, 113, etc.]
        self._errorsIgnoredByUser = userConfig.projectConfig.errorsIgnoredByUser

        self._setup(userConfig, log, accountCode, rootFolderPath, singleTrader, data, timeGenerator, self.name, False)

        # noinspection PyAttributeOutsideInit
        self._dataProvider = dataProvider

        self._log.debug(__name__ + '::setup_this_client')
        self.setRunningMode(LiveBacktest.BACKTEST)  # IBCpp function

        # noinspection PyAttributeOutsideInit
        self._transactionLog = transactionLog

        # noinspection PyAttributeOutsideInit
        # A function to simulate/calculate transaction commission
        self._simulate_commission = simulate_commission

    @property
    def name(self):
        return BrokerClientName.LOCAL

    @property
    def brokerName(self):
        return BrokerName.LOCAL

    def get_new_TD_refresh_token(self):
        raise NotImplementedError(self.name)

    def isConnectedWrapper(self):
        raise NotImplementedError(self.name)

    def reqHeartBeatsWrapper(self):
        raise NotImplementedError(self.name)

    def get_TD_access_token_expiry_in_days(self):
        raise NotImplementedError(self.name)

    def reqOneOrderWrapper(self, ibpyOrderId):
        raise NotImplementedError(self.name)

    def reqAccountSummaryWrapper(self, reqId, group, tag):
        raise NotImplementedError(self.name)

    def cancelMktDataWrapper(self, reqId):
        raise NotImplementedError(self.name)

    def reqRealTimeBarsWrapper(self, reqId, contract, barSize, whatToShow, useRTH):
        raise NotImplementedError(self.name)

    def reqContractDetailsWrapper(self, reqId, contract):
        raise NotImplementedError(self.name)

    def calculateImpliedVolatilityWrapper(self, reqId, contract, optionPrice, underPrice):
        raise NotImplementedError(self.name)

    def reqScannerSubscriptionWrapper(self, reqId, subscription):
        raise NotImplementedError(self.name)

    def cancelScannerSubscriptionWrapper(self, tickerId):
        raise NotImplementedError(self.name)

    def reqScannerParametersWrapper(self):
        raise NotImplementedError(self.name)

    def _sendHistoricalData(self, hist, reqId):
        self._log.debug(__name__ + '::_sendHistoricalData: reqId=%s' % (reqId,))
        for idx in hist.index:

            # It is possible that multiple rows have the same timestamp from the hist csv provided by clients.
            if isinstance(hist.loc[idx], pd.DataFrame):
                row = hist.loc[idx].iloc[-1]  # When it happens, use the last row
            else:
                row = hist.loc[idx]
            bar = {}
            bar['date'] = str(idx)
            bar['high'] = float(row['high'])
            bar['low'] = float(row['low'])
            bar['open'] = float(row['open'])
            bar['close'] = float(row['close'])
            bar['wap'] = 0
            bar['volume'] = int(row['volume'])
            bar = json.dumps(bar)
            self.simulateHistoricalData(reqId, bar)
        self.historicalDataEnd(reqId, str(hist.index[0]), str(hist.index[-1]))

    def cancelOrderWrapper(self, ibpyOrderId):
        int_orderId = self._idConverter.fromBrokerToIB(ibpyOrderId)
        self._log.info('cancelOrder is sent to %s ibpyOrderId=%s' % (self.name, ibpyOrderId))

        # All orders in OCA group will be deleted here
        self._orderToBeProcessed.cancel_order(int_orderId)

        # Send out order status of all canceled orders
        ibcpp_contract, ibcpp_order = self._orderToBeProcessed.get_by_orderId(int_orderId)
        if ibcpp_order is None:
            return
        # noinspection PyUnresolvedReferences
        if ibcpp_order.get('ocaGroup', None):
            # noinspection PyUnresolvedReferences
            orders_to_update = self._orderToBeProcessed.get_by_oca_group(ibcpp_order.ocaGroup)
        else:
            orders_to_update = [int_orderId]
        for order_id in orders_to_update:
            self.simulateOrderStatus(order_id, OrderStatus.CANCELLED, '0', '0', 0.0, 0, 0, 0.0, 0, 'empty', 0.0)

        self.error(int_orderId, 202, 'cancel order is confirmed', '')

    def connectWrapper(self):
        self._log.debug(__name__ + '::connectWrapper')
        return True

    def disconnectWrapper(self):
        self._log.debug(__name__ + '::disconnectWrapper')

    def reqCurrentTimeWrapper(self):
        tmp = dt_to_epoch(self._timeGenerator.get_current_time())
        # print(__name__ + '::reqCurrentTimeWrapper: invoke self.simulateCurrentTime')
        self.simulateCurrentTime(int(tmp))  # IBCpp function

    def reqIdsWrapper(self):
        self.simulateNextValidId(1)

    def reqMktDataWrapper(self, reqId, contract, genericTickList, snapshot):
        """
        Just ignore reqMktData because the real time prices will be simulated
        :param reqId:
        :param contract:
        :param genericTickList:
        :param snapshot:
        :return:
        """
        self._log.debug(__name__ + '::reqMktDataWrapper: reqId=%s contract=%s genericTickList=%s snapshot=%s'
                        % (str(reqId, ), print_IBCpp_contract(contract), str(genericTickList), str(snapshot)))
        self._activeRequests.set_a_request_of_a_reqId_to_a_status(reqId, ReqAttr.Status.COMPLETED)
        self.processMessagesWrapper(self._timeGenerator.get_current_time())

    def reqPositionsWrapper(self):
        """
        Just ignore the request because initial positions will be set up.
        :return:
        """
        self._log.debug(__name__ + '::reqPositionsWrapper')
        self.simulatePositionEnd()

    def reqAccountUpdatesWrapper(self, subscribe, accountCode):
        """
        In the backtest mode, just ignore this request
        Init accountUpdates will be simulated
        Later accountUpdates will be simulated when order is executed.
        :param subscribe:
        :param accountCode:
        :return:
        """
        self._log.debug(
            __name__ + '::reqAccountUpdatesWrapper: subscribe=%s accountCode=%s' % (str(subscribe), accountCode))
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAccountUpdates', ReqAttr.Status.COMPLETED)

    def reqAllOpenOrdersWrapper(self):
        """
        Just ignore the request because initial orders will be set up.
        :return:
        """
        self._log.debug(__name__ + '::reqAllOpenOrdersWrapper')
        self.simulateOpenOrderEnd()

    def reqHistoricalDataWrapper(self, reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        self._log.debug(__name__ + f'::reqHistoricalDataWrapper: reqId={reqId} endTime={endTime} goBack={goBack} formatDate={format}')
        if endTime == '':
            # endTime='' is acceptable for clientIB, but not for brokerClient_Local
            # When endTime is processed, it will be converted to string from datetime.
            # However, the strptime function has difficulty with some timezones, for example, 'EDT'
            # The safe way is to convert to UTC first.
            endTime = self._timeGenerator.get_current_time().astimezone(pytz.timezone('UTC'))
            endTime = dt.datetime.strftime(endTime, "%Y%m%d %H:%M:%S %Z")  # datetime -> string

        security = from_contract_to_security(contract)
        try:
            hist = self._dataProvider.provide_historical_data_from_local_variable_hist(security, endTime, goBack, barSize, whatToShow, useRTH)
        except NotEnoughHist:
            if self.getDataProvider().name != DataProviderName.LOCAL_FILE:
                self._log.info('Cannot find ingested hist for security=%s endTime=%s goBack=%s barSize=%s' % (security, endTime, goBack, barSize))
                self._log.info('IBridgePy has to request historical data from broker %s to continue backtesting but it will be slow. Recommend to add HistIngestPlan in TEST_ME.py' % (self.getDataProvider().name,))
                hist = self._dataProvider.provide_hist_from_a_true_dataProvider(security, endTime, goBack, barSize, whatToShow, useRTH)
            else:
                self._log.error('Cannot find ingested hist for security=%s endTime=%s goBack=%s barSize=%s' % (security, endTime, goBack, barSize))
                self._log.error('Please check if hist of security=%s barSize=%s has been ingested correctly.' % (security, barSize))
                self._log.error('Also, please verify if endTime=%s stays in between 1st line and last line.' % (endTime,))
                raise NotEnoughHist
        except RuntimeError as err:
            self._log.info(f'Unexpected error={err}')
            raise NotEnoughHist

        if not len(hist):
            if not endTime:
                endTime = self._timeGenerator.get_current_time().astimezone(pytz.timezone('UTC'))
            self._log.info('Cannot find ingested hist for security=%s endTime=%s goBack=%s barSize=%s' % (security, endTime, goBack, barSize))
            raise NotEnoughHist

        # completion signals here
        self._sendHistoricalData(hist, reqId)

    # noinspection PyUnresolvedReferences
    def simulate_process_order(self, timeNow):  # to simulate placing order
        active_orderId_list = self._orderToBeProcessed.get_active_orderId_list()
        self._log.notset(__name__ + '::simulate_process_order: timeNow=%s active_orderId_list=%s' % (timeNow, active_orderId_list))
        if len(active_orderId_list) == 0:
            return
        for int_orderId in active_orderId_list:
            contract, order = self._orderToBeProcessed.get_by_orderId(int_orderId)
            # print(f'{__name__}::simulate_process_order: order={order}')

            # Filling an order may change the content of active_orderId_list
            # For example, an order with stoploss and takeprofit.
            # When stoploss or takeprofit is filled, the other order should be canceled.
            if contract is None:
                continue
            if Decimal(order['totalQuantity']) == Decimal(0):
                self.simulateOrderStatus(int_orderId, 'Filled', str(order['totalQuantity']), '0', 0.0, 0, 0, 0.0, 0, 'empty', 0.0)
                self._orderToBeProcessed.fill_order(int_orderId)
                continue

            security = from_contract_to_security(contract)

            ask_price, bid_price, high_price, low_price = \
                self._dataProvider.provide_real_time_price_from_local_variable_hist(security, timeNow, [IBCpp.TickType.ASK, IBCpp.TickType.BID, IBCpp.TickType.HIGH, IBCpp.TickType.LOW])

            # print(ask_price, bid_price, high_price, low_price)
            # print(print_IBCpp_order(order))
            flag = False  # if an order meets the processing conditions
            # based on the current prices, decide which pending orders should be processed/simulated this round.
            ex_price = 0.0  # avoid PEP8 warning
            if order['orderType'] == 'MKT':  # for MKT order, just Fill it
                if order['action'] == 'BUY':
                    ex_price = ask_price
                else:
                    ex_price = bid_price
                flag = True
            elif order['orderType'] == 'LMT':
                # always assume simulation sequence: ask_price -> low_price -> high_price -> close_price
                if order['action'] == 'BUY':
                    if order['lmtPrice'] >= ask_price:
                        flag = True
                        ex_price = order['lmtPrice']
                    elif low_price <= order['lmtPrice'] < ask_price:
                        flag = True
                        ex_price = order['lmtPrice']
                    else:
                        flag = False
                else:  # SELL
                    # print('SELLING', order.lmtPrice, ask_price)
                    if order['lmtPrice'] <= ask_price:
                        flag = True
                        ex_price = order['lmtPrice']
                    elif ask_price < order['lmtPrice'] <= high_price:
                        flag = True
                        ex_price = order['lmtPrice']
                    else:
                        flag = False

            elif order['orderType'] == 'STP':
                ex_price = order['auxPrice']
                if order['action'] == 'BUY':
                    if order['auxPrice'] <= ask_price:
                        flag = True
                        ex_price = ask_price
                    elif ask_price < order['auxPrice'] <= high_price:
                        flag = True
                        ex_price = order['auxPrice']
                    else:
                        flag = False
                else:
                    # print('SELL STP', order.auxPrice, bid_price)
                    if order['auxPrice'] >= bid_price:
                        flag = True
                        ex_price = bid_price
                    elif low_price <= order['auxPrice'] < bid_price:
                        flag = True
                        ex_price = order['auxPrice']
                    else:
                        flag = False
            else:
                self._log.error(__name__ + '::simulate_process_order: cannot handle order.orderType = %s' % (order['orderType'],))
                exit()

            # this order should be processed/simulated right now
            if flag and ex_price > 0.001:
                self.simulateOrderStatus(int_orderId, 'Filled', str(order['totalQuantity']), '0', 0.0, 0, 0, 0.0, 0, 'empty', 0.0)
                self._orderToBeProcessed.fill_order(int_orderId)

                # Lets update status of all canceled orders
                orders_to_update = None
                ibcpp_contract, ibcpp_order = self._orderToBeProcessed.get_by_orderId(int_orderId)
                if ibcpp_order is not None:
                    if ibcpp_order['ocaGroup']:
                        orders_to_update = self._orderToBeProcessed.get_by_oca_group(ibcpp_order.ocaGroup)
                if order.get('parentId', None) not in [0, None] and orders_to_update is not None:
                    for order_id in orders_to_update:
                        if order_id != int_orderId:
                            self.simulateOrderStatus(order_id, OrderStatus.CANCELLED, '0', '0', 0.0, 0, 0, 0.0, 0, 'empty', 0.0)

                # after an order is executed, need to simulate execDetails (call-back function)
                execution = {}
                execution['acctNumber'] = order['account']
                execution['orderId'] = int_orderId
                if order['action'] == 'BUY':
                    execution['side'] = 'BOT'
                else:
                    execution['side'] = 'SLD'
                execution['shares'] = order['totalQuantity']
                execution['price'] = ex_price
                execution['orderRef'] = order.get('orderRef', None)

                # Only simulate transaction commission here. Do not simulate TotalCashValue because it is done in execDetails.
                transactionAmount = float(execution['shares']) * execution['price']
                currentCashValue = self._singleTrader.get_account_info(self.brokerName, self._accountCode, 'TotalCashValue')
                commission = roundToMinTick(self._simulate_commission(float(execution['shares'])))
                if (execution['side'] == 'BOT' and currentCashValue > commission + transactionAmount) or execution['side'] == 'SLD':
                    currentCashValue -= commission
                    self._log.info(f'Deduct commission={commission}')
                    self.updateAccountValue('TotalCashValue', currentCashValue, 'USD', self._accountCode)
                else:
                    self._log.error(f'EXIT, not enough fund for transaction={print_IBCpp_execution(execution)}: currentCashValue={currentCashValue} commission={commission}')
                    raise NotEnoughFund

                self.simulateExecDetails(-1, json.dumps(contract), json.dumps(execution), from_contract_to_security(contract).full_print())

                # IBCpp::simulatePosition needs more calculation because it needs to consider the current
                # positions.
                oldPosition = self._singleTrader.get_position(self.name, self._accountCode, security)
                # print(__name__ + '::simulate_process_order:: oldPosition=%s' % (position,))
                oldPrice = oldPosition.price
                hold = oldPosition.amount
                amount = None
                price = None
                if order['action'] == 'BUY':
                    if Decimal(hold) + Decimal(order['totalQuantity']) != Decimal(0):
                        price = (Decimal(oldPrice) * Decimal(hold) + Decimal(ex_price) * Decimal(order['totalQuantity'])) / (Decimal(hold) + Decimal(order['totalQuantity']))
                    else:
                        price = 0.0
                    amount = Decimal(hold) + Decimal(order['totalQuantity'])

                elif order['action'] == 'SELL':
                    if Decimal(hold) == Decimal(order['totalQuantity']):
                        price = 0.0
                    else:
                        price = (Decimal(oldPrice) * Decimal(hold) - Decimal(ex_price) * Decimal(order['totalQuantity'])) / (Decimal(hold) - Decimal(order['totalQuantity']))
                    amount = Decimal(hold) - Decimal(order['totalQuantity'])
                self._log.debug(f'{__name__}::simulate_process_order: account={order["account"]} contract={contract} amount={amount} price={price}')
                self.simulatePosition(order['account'], json.dumps(contract), str(amount), float(price), from_contract_to_security(contract).full_print())
                self._transactionLog.info(f'{self._timeGenerator.get_current_time()} {execution["orderId"]} {from_contract_to_security(contract).full_print()} {execution["side"]} {execution["shares"]} {execution["price"]}')
                # Do not need to update TotalCashValue because TotalCashValue is updated in execDetails
                # Do not update NetLiquidation and GrossPositionValue here because there is no way to update GrossPositionValue that needs real time price to simulate.
                # These two values are updated in BrokerService_Local in processMessages

    def modifyOrderWrapper(self, contract, order, ibpyRequest):
        self.placeOrderWrapper(contract, order, ibpyRequest)

    def placeOrderWrapper(self, contract, order, ibpyRequest):
        self._log.debug(__name__ + '::placeOrderWrapper: contract=%s order=%s' % (print_IBCpp_contract(contract), print_IBCpp_order(order)))

        if isinstance(order.get('orderId', None), int):
            int_orderId = order['orderId']
        else:
            int_orderId = self.use_next_id()
            order['orderId'] = int_orderId

        # Set for ending flat.
        # Otherwise, the following line in broker_client_factory::CallBacks::orderStatus will not be able to find a reqId
        # reqId = self.activeRequests.find_reqId_by_int_orderId(int_orderId)
        ibpyRequest.param['int_orderId'] = int_orderId

        ibpyOrderId = self._idConverter.fromIBtoBroker(int_orderId)

        # Register ibpyOrderId in SingleTrader so that it can search accountCode by incoming int_orderId
        self._singleTrader.set_from_send_req_to_server(self.name, order['account'], ibpyOrderId)

        self._orderToBeProcessed.add_order(int_orderId, contract, order)
        self.simulateOpenOrder(int_orderId, json.dumps(contract), json.dumps(order), '', from_contract_to_security(contract).full_print())  # IBCpp function
        self.simulateOrderStatus(int_orderId, 'Submitted', '0', str(order['totalQuantity']), 0.0, 0, 0, 0.0, 0, 'empty', 0.0)  # IBCpp function
        # Should not simulate process order immediately after place order because slOrder and tpOrder will be added
        # by different placeOrder()
        # self.simulate_process_order(self.get_datetime())

    def processMessagesWrapper(self, timeNow):
        self._log.notset(__name__ + '::processMessagesWrapper: timeNow=%s' % (timeNow,))
        self.simulate_process_order(timeNow)
        """
        # DO NOT DELETE. Save for reference. 20210522
        # !!! Change to lazy provider, supply values per requested
        tempDict = self.realTimePriceRequestedList.getAllStrSecurity()
        if len(tempDict) == 0:
            # self._log.error(__name__ + '::processMessagesWrapper: EXIT, no real time prices are requested yet')
            return True  # run Trader::repeat_function

        for str_security in tempDict:
            try:
                open_price, high_price, low_price, close_price, volume = \
                    self._dataProvider.get_real_time_price(str_security, timeNow,
                                                          [IBCpp.TickType.OPEN, IBCpp.TickType.HIGH,
                                                           IBCpp.TickType.LOW, IBCpp.TickType.CLOSE,
                                                           IBCpp.TickType.VOLUME])
            except AssertionError:
                self._log.error(
                    __name__ + '::processMessagesWrapper: str_security=%s timeNow=%s' % (str_security, timeNow))
                return False  # DO NOT run Trader::repeat_function because dataFromServer is not available

            reqId = tempDict[str_security]
            self.simulateTickPrice(reqId, IBCpp.TickType.OPEN, open_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.HIGH, high_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.LOW, low_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.CLOSE, close_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.LAST, close_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.ASK, close_price, False, str_security)
            self.simulateTickPrice(reqId, IBCpp.TickType.BID, close_price, False, str_security)
            self.simulateTickSize(reqId, IBCpp.TickType.VOLUME, int(volume), str_security)
        return True  # run Trader::repeat_function because all dataFromServer is loaded
        """

    def add_exchange_to_security(self, security):
        """
        For brokerClientLocal, NO need to add exchange because the keys in dataProviderLocal.hist is
        str_security_without_exchange_primaryExchange
        :param security:
        :return:
        """
        pass

    def add_primaryExchange_to_security(self, security):
        """
        For brokerClientLocal, NO need to add primaryExchange because the keys in dataProviderLocal.hist is
        str_security_without_exchange_primaryExchange
        :param security:
        :return:
        """
        pass
