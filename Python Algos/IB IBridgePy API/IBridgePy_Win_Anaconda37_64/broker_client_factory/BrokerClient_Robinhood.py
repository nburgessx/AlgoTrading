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

from BasicPyLib.BasicTools import dt_to_epoch, epoch_to_dt
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.IbridgepyTools import symbol
from IBridgePy.constants import LiveBacktest, OrderStatus, OrderType, OrderTif, OrderAction, \
    BrokerClientName, BrokerName
from IBridgePy.quantopian import from_security_to_contract, from_contract_to_security
from broker_client_factory.BrokerClientDefs import ReqAttr
from broker_client_factory.CallBacks import CallBacks
from models.utils import print_IBCpp_contract


class OrderTypeConverter(object):
    def __init__(self):
        pass

    @staticmethod
    def fromRBtoIB(orderType, trigger):
        if orderType == 'market' and trigger == 'immediate':
            return OrderType.MKT
        if orderType == 'market' and trigger == 'stop':
            return OrderType.STP
        if orderType == 'limit' and trigger == 'immediate':
            return OrderType.LMT
        if orderType == 'limit' and trigger == 'stop':
            return OrderType.STP_LMT
        else:
            print(__name__ + '::OrderTypeConverter: EXIT, cannot handle orderType=%s trigger=%s' % (orderType, trigger))
            exit()


class OrderStatusConverter(object):
    def __init__(self):
        pass

    @staticmethod
    def fromRBtoIB(orderStatus):
        if orderStatus == 'filled':
            return OrderStatus.FILLED
        elif orderStatus == 'cancelled':
            return OrderStatus.CANCELLED
        elif orderStatus in ['queued', 'confirmed', 'partially_filled', 'unconfirmed']:
            return OrderStatus.SUBMITTED
        elif orderStatus in ['rejected', 'failed']:
            return OrderStatus.INACTIVE
        else:
            print(__name__ + '::OrderStatusConverter::fromRBtoIB: EXIT, Robinhood cannot handle orderStatus=%s' % (orderStatus,))
            exit()


class BarSizeConverter(object):
    def __init__(self):
        pass

    @staticmethod
    def fromIBtoRB(barSize):
        # 1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins, 30 mins, 1 hour, 1 day
        if barSize == '10 min':
            return '10minute'
        elif barSize == '5 mins':
            return '5minute'
        elif barSize == '1 day':
            return 'day'
        else:
            print(__name__ + '::BarSizeConverter::fromIBtoRB: EXIT, Robinhood cannot handle barSize=%s' % (barSize,))
            exit()


class GoBackConverter(object):
    def __init__(self):
        pass

    @staticmethod
    def fromIBtoRB(goBack):
        count = None
        if 'D' in goBack:
            count = int(goBack[:-2])
        elif 'W' in goBack:
            count = int(goBack[:-2]) * 7
        elif 'M' in goBack:
            count = int(goBack[:-2]) * 30
        elif 'Y' in goBack:
            count = int(goBack[:-2]) * 365

        if count <= 1:
            return 'day'
        elif count <= 7:
            return 'week'
        elif count <= 365:
            return 'year'
        elif count <= 365 * 5:
            return '5year'
        else:
            return 'all'


class OrderTifConverter(object):
    def __init__(self):
        pass

    @staticmethod
    def fromIBtoRB(tif):
        if tif == OrderTif.GTC:
            return 'GTC'
        elif tif == OrderTif.DAY:
            return 'GFD'
        else:
            print(__name__ + '::OrderTifConverter::fromIBtoTD: EXIT, cannot handle tif=%s' % (tif,))
            exit()

    @staticmethod
    def fromRBtoIB(tif):
        if tif == 'gtc':
            return OrderTif.GTC
        elif tif == 'gfd':
            return OrderTif.DAY
        else:
            print(__name__ + '::OrderTifConverter::fromTDtoIB: EXIT, cannot handle tif=%s' % (tif,))
            exit()


class OrderActionConverter(object):
    def __init__(self):
        pass

    @staticmethod
    def fromRBtoIB(action):
        if action == 'buy':
            return OrderAction.BUY
        elif action == 'sell':
            return OrderAction.SELL
        else:
            print(__name__ + '::OrderActionConverter::fromRBtoIB: EXIT, cannot handle action=%s' % (action,))
            exit()

    @staticmethod
    def fromIBtoRB(action):
        if action == 'BUY':
            return OrderAction.BUY
        elif action == 'SELL':
            return OrderAction.SELL
        else:
            print(__name__ + '::OrderActionConverter::fromIBtoRB: EXIT, cannot handle action=%s' % (action,))
            exit()


class OrderConverter(object):
    def __init__(self):
        pass

    @staticmethod
    def fromRBtoIBOpenOrder(rbOrder, idConverter, accountCode):
        # IBCpp.Order().orderId must be an integer so that an integer orderId has to be created
        originalTdOrderId = str(rbOrder['id'])
        int_orderId = idConverter.fromBrokerToIB(originalTdOrderId)

        security = symbol(str(rbOrder['symbol']))
        contract = from_security_to_contract(security)
        orderStatus = OrderStatusConverter().fromRBtoIB(str(rbOrder['state']))
        quantity = int(float(rbOrder['quantity']))

        orderState = IBCpp.OrderState()
        orderState.status = orderStatus

        ibOrder = IBCpp.Order()
        ibOrder.orderId = int_orderId
        ibOrder.account = accountCode
        ibOrder.action = OrderActionConverter().fromRBtoIB(str(rbOrder['side']))  # _robinhoodClient side : buy, sell
        ibOrder.totalQuantity = quantity
        ibOrder.orderType = OrderTypeConverter().fromRBtoIB(str(rbOrder['type']).lower(), str(rbOrder['trigger']).lower())
        ibOrder.tif = OrderTifConverter().fromRBtoIB(str(rbOrder['time_in_force']))
        if ibOrder.orderType == OrderType.LMT:
            ibOrder.lmtPrice = float(str(rbOrder['price']))
        elif ibOrder.orderType == OrderType.STP:
            ibOrder.auxPrice = float(str(rbOrder['stop_price']))
        elif ibOrder.orderType == OrderType.STP_LMT:
            ibOrder.lmtPrice = float(str(rbOrder['price']))
            ibOrder.auxPrice = float(str(rbOrder['stop_price']))
        elif ibOrder.orderType == OrderType.MKT:
            pass
        else:
            print(__name__ + '::reqOneOrderWrapper: EXIT, cannot handle orderType=%s' % (ibOrder.orderType,))
            exit()
        return int_orderId, contract, ibOrder, orderState, security

    @staticmethod
    def fromRBtoIBOrderStatus(rbOrder):
        orderStatus = OrderStatusConverter().fromRBtoIB(str(rbOrder['state']))
        quantity = int(float(rbOrder['quantity']))
        filledQuantity = int(float(rbOrder['cumulative_quantity']))
        remaining = quantity - filledQuantity
        whyHeld = str(rbOrder['reject_reason'])
        price = float(str(rbOrder['price']))
        return orderStatus, filledQuantity, remaining, price, whyHeld

    @staticmethod
    def fromIBtoRB(contract, order):
        """
        Robinhood client is implemented by calling functions to place orders. See broker_client_factory::Robinhood::Robinhood
        :param contract:
        :param order:
        :return:
        """
        raise NotImplementedError


# noinspection PyAbstractClass
class BrokerClientRobinhood(CallBacks):
    # !!!
    # DO NOT implement __init___ here. It will override IBCpp.__init__ and cause many errors
    @property
    def name(self):
        return BrokerClientName.ROBINHOOD

    @property
    def brokerName(self):
        return BrokerName.ROBINHOOD

    def setup_this_client(self, userConfig, log, rootFolderPath, singleTrader, dataFromServer, timeGenerator,
                          robinhoodClient, accountCode, username, password, qrCode=None):
        self.setRunningMode(LiveBacktest.LIVE)  # IBCpp function

        # noinspection PyAttributeOutsideInit
        self._robinhoodClient = robinhoodClient
        # noinspection PyAttributeOutsideInit
        self._username = username
        # noinspection PyAttributeOutsideInit
        self._password = password
        # noinspection PyAttributeOutsideInit
        self._qrCode = qrCode

        # Clients want to ignore some errors from the broker, instead of terminating the code.
        # It should be a list of error codes, such as [112, 113, etc.]
        self._errorsIgnoredByUser = userConfig.projectConfig.errorsIgnoredByUser

        self._setup(userConfig, log, accountCode, rootFolderPath, singleTrader, dataFromServer, timeGenerator, self.name, False, errorsIgnoredByUser)
        self._log.debug(__name__ + '::setup_this_client')

    def isConnectedWrapper(self):
        self._log.debug(__name__ + '::isConnectedWrapper')
        raise NotImplementedError

    def connectWrapper(self):
        self._log.debug(__name__ + '::connectWrapper')
        return self._robinhoodClient.login(self._username, self._password, self._qrCode)

    def disconnectWrapper(self):
        self._log.debug(__name__ + '::disconnectWrapper')
        self._robinhoodClient.logout()

    def reqPositionsWrapper(self):
        ans = self._robinhoodClient.get_all_positions()
        # ans = [{'symbol':'SPY', 'quantity':100, 'average_buy_price':99.9}]
        for position in ans:
            security = symbol(str(position['symbol']))
            contract = from_security_to_contract(security)
            self.position(self._accountCode, contract, int(float(position['quantity'])), float(position['average_buy_price']))
        self.simulatePositionEnd()

    def reqCurrentTimeWrapper(self):
        tmp = dt_to_epoch(self._timeGenerator.get_current_time())
        self._log.debug(__name__ + '::reqCurrentTimeWrapper: tmp=%s' % (tmp,))
        self.simulateCurrentTime(int(tmp))  # IBCpp function

    def _convert_order(self, rbOrder):
        int_orderId, contract, ibOrder, orderState, security = OrderConverter().fromRBtoIBOpenOrder(rbOrder, self._idConverter, self._accountCode)
        # IBCpp function
        self.simulateOpenOrder(int_orderId, contract, ibOrder, orderState, security.full_print())
        orderStatus, filledQuantity, remaining, price, whyHeld = OrderConverter.fromRBtoIBOrderStatus(rbOrder)
        # IBCpp function
        self.simulateOrderStatus(int_orderId,
                                 orderStatus,
                                 filledQuantity,  # filled
                                 remaining,  # remaining
                                 price,  # avgFillPrice
                                 0,  # permId
                                 0,  # parentId
                                 0,  # lastFillPrice
                                 0,  # clientId
                                 whyHeld)  # whyHeld

    def reqOneOrderWrapper(self, ibpyOrderId):
        assert(isinstance(ibpyOrderId, str))
        order = self._robinhoodClient.get_one_order(ibpyOrderId)
        if 'error' in order:
            self._log.error(__name__ + '::reqOneOrderWrapper: EXIT, cannot found ibpyOrderId=%s. Please verify it.' % (ibpyOrderId,))
            exit()
        self._convert_order(order)
        self.simulateOpenOrderEnd()

    def reqAllOpenOrdersWrapper(self):
        ans = self._robinhoodClient.get_all_orders()
        for rbOrder in ans:
            self._convert_order(rbOrder)
        self.simulateOpenOrderEnd()

    def reqAccountUpdatesWrapper(self, subscribe, accountCode):
        ans = self._robinhoodClient.portfolios()
        correctAccountCode = str(ans['account']).split('/')[-2]
        if accountCode != correctAccountCode:
            self._log.error(__name__ + '::reqAccountUpdatesWrapper: EXIT, input accountCode=%s is not correct, it should be %s' % (accountCode, correctAccountCode))
            exit()
        self.simulateUpdateAccountValue('NetLiquidation', str(ans['last_core_equity']), 'USD', accountCode)
        self.simulateUpdateAccountValue('TotalCashValue', str(ans['withdrawable_amount']), 'USD', accountCode)
        self.simulateUpdateAccountValue('GrossPositionValue', str(ans['market_value']), 'USD', accountCode)
        self._activeRequests.set_all_requests_of_a_reqType_to_a_status('reqAccountUpdates', ReqAttr.Status.COMPLETED)

    def reqAccountSummaryWrapper(self, reqId, group, tag):
        raise NotImplementedError

    def reqIdsWrapper(self):
        self.simulateNextValidId(1)

    def reqHistoricalDataWrapper(self, reqId, contract, endTime, goBack, barSize, whatToShow, useRTH, formatDate):
        if barSize not in ['1 day', '5 mins', '10 mins']:
            self._log.error(__name__ + '::reqHistoricalDataWrapper: EXIT, Robinhood does not support barSize=%s'
                            % (barSize,))
        interval = BarSizeConverter().fromIBtoRB(barSize)
        span = GoBackConverter().fromIBtoRB(goBack)
        self._log.notset(__name__ + '::reqHistoricalDataWrapper: contract=%s interval=%s span=%s'
                         % (print_IBCpp_contract(contract), interval, span))
        ans = self._robinhoodClient.get_historical_quotes(contract.symbol,
                                                          interval,
                                                          span)

        hist = None
        try:
            hist = ans['results'][0]['historicals']
        except KeyError:
            self._log.error(__name__ + '::reqHistoricalDataWrapper: EXIT, ans=%s' % (ans,))
            exit()

        for row in hist:
            t = dt.datetime.strptime(row['begins_at'], "%Y-%m-%dT%H:%M:%SZ")
            epoc = dt_to_epoch(t)
            if formatDate == 2:
                date = epoc
            else:
                date = epoch_to_dt(float(epoc))
                date = date.strftime("%Y%m%d  %H:%M:%S")  # Must be UTC because requested time was cast to UTC

            self.simulateHistoricalData(reqId,
                                        str(date),
                                        float(row['open_price']),
                                        float(row['high_price']),
                                        float(row['low_price']),
                                        float(row['close_price']),
                                        int(float(row['volume'])),
                                        1,  # barCount
                                        0.0,  # WAP
                                        1)  # hasGap
        self.simulateHistoricalData(reqId, 'finished', 0.0, 0.0, 0.0, 0.0, 1, 1, 0.0, 1)

    def reqMktDataWrapper(self, reqId, contract, genericTickList, snapshot):
        ans = self._robinhoodClient.get_quote(str(contract.symbol))
        str_security = from_contract_to_security(contract).full_print()

        self.simulateTickPrice(reqId, IBCpp.TickType.ASK, float(ans['ask_price']), True, str_security)
        self.simulateTickPrice(reqId, IBCpp.TickType.BID, float(ans['bid_price']), True, str_security)
        self.simulateTickPrice(reqId, IBCpp.TickType.LAST, float(ans['last_trade_price']), True, str_security)
        self.simulateTickPrice(reqId, IBCpp.TickType.CLOSE, float(ans['previous_close']), True, str_security)
        self.simulateTickSize(reqId, IBCpp.TickType.ASK_SIZE, int(ans['ask_size']), str_security)
        self.simulateTickSize(reqId, IBCpp.TickType.BID_SIZE, int(ans['bid_size']), str_security)

    def cancelMktDataWrapper(self, reqId):
        raise NotImplementedError

    def reqRealTimeBarsWrapper(self, reqId, contract, barSize, whatToShow, useRTH):
        raise NotImplementedError

    # noinspection DuplicatedCode
    def placeOrderWrapper(self, contract, order, ibpyRequest):
        instrument = self._robinhoodClient.instruments(contract.symbol)[0]
        action = OrderActionConverter().fromIBtoRB(order.action)
        tif = OrderTifConverter().fromIBtoRB(order.tif)
        quantity = int(order.totalQuantity)
        ans = None
        if order.orderType == OrderType.MKT:
            ans = self._robinhoodClient.place_market_order(action, instrument, quantity, tif)
        elif order.orderType == OrderType.LMT:
            ans = self._robinhoodClient.place_limit_order(action,
                                                          instrument=instrument,
                                                          limit_price=order.lmtPrice,
                                                          quantity=quantity,
                                                          time_in_force=tif)
        elif order.orderType == OrderType.STP:
            ans = self._robinhoodClient.place_stop_order(action,
                                                         instrument=instrument,
                                                         stop_price=order.auxPrice,
                                                         quantity=quantity,
                                                         time_in_force=tif)
        else:
            self._log.error(__name__ + '::placeOrderWrapper: EXIT, cannot handle orderType=%s' % (order.orderType,))
            exit()
        ibpyOrderId = str(ans['id'])
        self._log.info('Order was placed to %s successfully. ibpyOrderId=%s' % (self.name, ibpyOrderId))

        # Register int_orderId in _idConverter so that brokerClient::CallBack::orderStatus knows how to handle int_orderId
        int_orderId = self._idConverter.fromBrokerToIB(ibpyOrderId)
        self._idConverter.setRelationship(int_orderId, ibpyOrderId)

        # Set for ending flat.
        # Otherwise, the following line in broker_client_factory::CallBacks::orderStatus will not be able to find a reqId
        # reqId = self.activeRequests.find_reqId_by_int_orderId(int_orderId)
        ibpyRequest.param['int_orderId'] = int_orderId

        # Register ibpyOrderId in SingleTrader so that it can search accountCode by incoming int_orderId
        self._singleTrader.set_from_send_req_to_server(self.name, order.account, ibpyOrderId)

        # IBCpp function
        order.orderId = int_orderId
        self.simulateOpenOrder(int_orderId, contract, order, IBCpp.OrderState(),
                               from_contract_to_security(contract).full_print())  # IBCpp function
        # IBCpp function, this is the ending flag for PlaceOrder
        self.simulateOrderStatus(int_orderId, 'Submitted', 0, order.totalQuantity, 0.0, 0, 0, 0, 0, '')

    def reqContractDetailsWrapper(self, reqId, contract):
        raise NotImplementedError

    def calculateImpliedVolatilityWrapper(self, reqId, contract, optionPrice, underPrice):
        raise NotImplementedError

    def reqScannerSubscriptionWrapper(self, reqId, subscription):
        raise NotImplementedError

    def cancelScannerSubscriptionWrapper(self, tickerId):
        raise NotImplementedError

    def cancelOrderWrapper(self, ibpyOrderId):
        if not isinstance(ibpyOrderId, str):
            self._log.error(__name__ + '::cancelOrderWrapper: EXIT, ibpyOrderId must be a string')
            exit()
        self.reqOneOrderWrapper(ibpyOrderId)  # Make sure it is a valid order and callback openOrder() to record order info at IBridgePy. Otherwise, error: get_accountCode_by_ibpyOrderId: EXIT, cannot find accountCode by ibpyOrderId
        self._log.info('cancelOrder is sent to %s ibpyOrderId=%s' % (self.name, ibpyOrderId))
        self._robinhoodClient.cancel_order(ibpyOrderId)
        self._log.info('ibpyOrderid=%s is canceled successfully' % (ibpyOrderId,))
        int_orderId = self._idConverter.fromBrokerToIB(ibpyOrderId)
        self.simulateOrderStatus(int_orderId, OrderStatus.CANCELLED, 0, 0, 0.0, 0, 0, 0, 0, '')
        self.error(int_orderId, 202, 'cancel order is confirmed')

    def reqScannerParametersWrapper(self):
        raise NotImplementedError

    def add_exchange_to_security(self, security):
        """
        For brokerClientLocal, NO need to add exchange because the keys in dataProvider.hist is
        str_security_without_exchange_primaryExchange
        :param security:
        :return:
        """
        pass

    def add_primaryExchange_to_security(self, security):
        """
        For brokerClientLocal, NO need to add primaryExchange because the keys in dataProvider.hist is
        str_security_without_exchange_primaryExchange
        :param security:
        :return:
        """
        pass
