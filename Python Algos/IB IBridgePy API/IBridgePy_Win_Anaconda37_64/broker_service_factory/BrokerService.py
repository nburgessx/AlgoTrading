# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""
import datetime as dt
from sys import exit
from decimal import Decimal

import pytz

# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.IbridgepyTools import stripe_exchange_primaryExchange_from_security, choose_whatToShow
from IBridgePy.constants import SymbolStatus, OrderStatus
from IBridgePy.quantopian import from_contract_to_security
from broker_client_factory.BrokerClientDefs import CancelOrder, ReqHistoricalData, PlaceOrder, ReqMktData, \
    ReqScannerSubscription, CancelScannerSubscription


class BrokerService(object):
    def __init__(self, userConfig, log, timeGenerator, singleTrader, dataFromServer):
        self._userConfig = userConfig
        self._log = log
        # timeGenerator, singleTrader, dataFromServer must be shared between brokerService and brokerClient
        # so that they are synced, singleton  TODO: make a singleton factory
        self._timeGenerator = timeGenerator
        self._singleTrader = singleTrader
        self._dataFromServer = dataFromServer
        self._log.notset(__name__ + '::__init__')

        # 20200927 BrokerService can be used as a DataProviderService to provide data from 3rd party data provider.
        # For example, TD can be a DataProviderService for IB BrokerService when no data package is purchased from IB.
        # The current design is to set it by invoking setAsDataProviderService method.
        # TODO: Refactor BrokerService to inherit from a Service, which has two child, DataService and BrokerService. IB, TD, Robinhood can be both of DataService and BrokerService.
        self._asDataProviderService = False

    @property
    def _brokerClient(self):
        return self._userConfig.brokerClient

    def __str__(self):
        return '{name=%s id=%s brokerClient=%s timeGenerator=%s}' % (self.name, id(self), self._brokerClient, self._timeGenerator)

    @property
    def name(self):
        """
        Name of the broker

        :return: string name
        """
        raise NotImplementedError(self.name)

    @property
    def brokerName(self):
        """
        Name of the broker

        :return: string name
        """
        raise NotImplementedError(self.name)

    @property
    def versionNumber(self):
        return self._brokerClient.versionNumber

    def getBrokerClient(self):
        return self._brokerClient

    def setAsDataProviderService(self):
        self._asDataProviderService = True

    def _get_account_info_one_tag(self, accountCode, tag, meta='value'):
        raise NotImplementedError

    def _get_real_time_price_from_dataFromServer(self, security, tickType):  # return real time price
        self._log.notset(__name__ + '::_get_real_time_price_from_dataFromServer: security=%s tickType=%s' % (security.full_print(), tickType))

        ans = self._dataFromServer.get_value(security, tickType, 'price')
        if ans is None:  # the request has been sent out but no callback value has been received yet. -1 = request is out but no real value yet.
            ans = -1
        self._log.debug(__name__ + '::_get_real_time_price_from_dataFromServer: security=%s tickType=%s returnedValue=%s' % (security, tickType, ans))
        return ans

    def _get_real_time_size_from_dataFromServer(self, security, tickType):  # return real time price
        self._log.debug(__name__ + '::_from_dataFromServer: security=%s tickType=%s' % (security, tickType))
        return self._dataFromServer.get_value(security, tickType, 'size')

    def _get_5_second_real_time_bar_from_dataFromServer(self, security):
        self._log.notset(f'{__name__}::_get_5_second_real_time_bar_from_dataFromServe: security={security}')
        return self._dataFromServer.get_5_second_real_time_bar(security)

    def _get_position(self, accountCode, security):
        """
        Guarantee to return a PositionRecord even if there is no current position.
        :param accountCode:
        :param security:
        :return: Guarantee to return a PositionRecord
        """
        adj_security = stripe_exchange_primaryExchange_from_security(security)
        self._log.debug(__name__ + '::_get_position: adj_security=%s' % (adj_security.full_print(),))
        return self._singleTrader.get_position(self.brokerName, accountCode, adj_security)

    def _get_all_positions(self, accountCode):
        allPositions = self._singleTrader.get_all_positions(self.brokerName, accountCode)
        ans = {}
        for str_security in allPositions:
            contract = allPositions[str_security].contract
            security = from_contract_to_security(contract)
            # adj_security = self.add_exchange_primaryExchange_to_security(security)
            # ans[adj_security] = allPositions[str_security]
            ans[security] = allPositions[str_security]
        return ans

    def _get_all_orders(self, accountCode):
        """

        :param accountCode:
        :return: dict Keyed by ibpyOrderId, value = models::Order::IbridgePyOrder
        """
        self._log.debug(__name__ + '::_get_all_orders: accountCode=%s' % (accountCode,))
        return self._singleTrader.get_all_orders(self.brokerName, accountCode)

    def add_exchange_primaryExchange_to_security(self, security):
        self._log.debug(__name__ + '::add_exchange_primaryExchange_to_security: security=%s' % (security.full_print(),))
        if security.symbolStatus == SymbolStatus.SUPER_SYMBOL:  # add superSymbol into security_info so that user does not need to write them in security_info.csv again
            self._brokerClient.append_security_info(security)
        else:
            self._brokerClient.add_primaryExchange_to_security(security)
            self._brokerClient.add_exchange_to_security(security)

    def cancel_order(self, ibpyOrderId):
        """
        Cancel order by its ibpyOrderId
        :param ibpyOrderId: string
        :return: None
        """
        self._log.debug(__name__ + '::cancel_order: ibpyOrderId=%s' % (ibpyOrderId,))
        self.submit_requests(CancelOrder(ibpyOrderId))

    def connect(self):
        self._log.debug(__name__ + '::connect')
        return self._brokerClient.connectWrapper()

    def disconnect(self):
        self._log.debug(f"{__name__}::disconnect: ")
        self._brokerClient.disconnectWrapper()

    # Only used by MarketManagerBase
    def get_next_time(self):
        self._log.notset(__name__ + '::get_next_time')
        return self._timeGenerator.get_next_time()

    def get_account_info(self, accountCode, tags, meta='value'):  # get account related info
        self._log.debug(__name__ + '::get_account_info: accountCode=%s tags=%s' % (accountCode, tags))
        if isinstance(tags, str):
            return self._get_account_info_one_tag(accountCode, tags, meta)
        elif isinstance(tags, list):
            ans = []
            for tag in tags:
                ans.append(self._get_account_info_one_tag(accountCode, tag, meta))
            return ans

    # Used by aTrader and
    def get_datetime(self):
        """
        Get IB server time
        :return: datetime in UTC timezone
        """
        ans = self._timeGenerator.get_current_time()
        self._log.notset(__name__ + '::get_datetime=%s' % (ans,))
        return ans

    def get_active_accountCodes(self):
        """
        get a list of accountCodes from IB server to check if the user-input accountCode is acceptable.
        :return:
        """
        self._log.debug(__name__ + '::get_active_accountCodes')
        return self._singleTrader.get_all_active_accountCodes(self.brokerName)

    def get_all_open_orders(self, accountCode):
        self._log.debug(__name__ + '::get_all_open_orders: accountCode=%s' % (accountCode,))
        allOrders = self.get_all_orders(accountCode)  # Return a dict, keyed by ibpyOrderId, value = models::Order::IbridgePyOrder
        ans = []
        for ibpyOrderId in allOrders:
            status = allOrders[ibpyOrderId].status
            if status in [OrderStatus.APIPENDING, OrderStatus.PENDINGSUBMIT, OrderStatus.PENDINGCANCEL,
                          OrderStatus.PRESUBMITTED, OrderStatus.SUBMITTED]:
                ans.append(allOrders[ibpyOrderId])
        return ans

    def get_all_orders(self, accountCode):
        raise NotImplementedError(self.name)

    def get_all_positions(self, accountCode):
        """
        Get all of positionRecords associated with the accountCode
        :param accountCode:
        :return: dictionary, keyed by Security object with exchange info!!!, value = PositionRecord
        """
        raise NotImplementedError(self.name)

    def get_contract_details(self, security, field, waitForFeedbackInSeconds=30):
        raise NotImplementedError(self.name)

    def get_heart_beats(self):
        return self._brokerClient.get_heart_beats()

    def get_ibpy_expiry_in_days(self):
        """

        :return: int, number of days of IBridgePy passcode to expiry
        """
        return self._brokerClient.get_authed_expiry()

    def get_scanner_results(self, waitForFeedbackInSeconds, kwargs):
        #        numberOfRows=-1, instrument='', locationCode='', scanCode='', abovePrice=0.0,
        #        belowPrice=0.0, aboveVolume=0, marketCapAbove=0.0, marketCapBelow=0.0, moodyRatingAbove='',
        #        moodyRatingBelow='', spRatingAbove='', spRatingBelow='', maturityDateAbove='', maturityDateBelow='',
        #        couponRateAbove=0.0, couponRateBelow=0.0, excludeConvertible=0, averageOptionVolumeAbove=0,
        #        scannerSettingPairs='', stockTypeFilter=''
        tagList = ['numberOfRows', 'instrument', 'locationCode', 'scanCode', 'abovePrice', 'belowPrice', 'aboveVolume',
                   'marketCapAbove',
                   'marketCapBelow', 'moodyRatingAbove', 'moodyRatingBelow', 'spRatingAbove', 'spRatingBelow',
                   'maturityDateAbove',
                   'maturityDateBelow', 'couponRateAbove', 'couponRateBelow', 'excludeConvertible',
                   'averageOptionVolumeAbove',
                   'scannerSettingPairs', 'stockTypeFilter']
        subscription = {}
        for ct in kwargs:
            if ct in tagList:
                subscription[ct] = kwargs[ct]

        reqIdList = self.submit_requests(ReqScannerSubscription(subscription, waitForFeedbackInSeconds=waitForFeedbackInSeconds))
        self.submit_requests(CancelScannerSubscription(reqIdList[0]))
        return self._brokerClient.get_submit_requests_result(reqIdList[0])  # return a pandas dataFrame

    def get_TD_access_token_expiry_in_days(self):
        return self._brokerClient.get_TD_access_token_expiry_in_days()

    def get_new_TD_refresh_token(self):
        return self._brokerClient.get_new_TD_refresh_token()

    def get_historical_data(self, security, barSize, goBack, endTime=None, whatToShow='', useRTH=1,
                            waitForFeedbackInSeconds=30, followUp=True):
        """
        :param followUp:
        :param security: Security
        :param barSize: string
        barSize can be any of the following values(string)
        1 sec, 5 secs,15 secs,30 secs,1 min,2 mins,3 mins,5 mins,15 mins,30 mins,1 hour,1 day
        :param goBack: string
        :param endTime: default value is '', IB server deems '' as the current server time.
        If user wants to supply a value, it must be a datetime with timezone
        :param whatToShow: string
        whatToShow: see IB documentation for choices
        TRADES,MIDPOINT,BID,ASK,BID_ASK,HISTORICAL_VOLATILITY,OPTION_IMPLIED_VOLATILITY
        :param useRTH: int 1=within regular trading hours, 0=ignoring RTH
        :param waitForFeedbackInSeconds:
        :return: a dataFrame, keyed by a datetime with timezone UTC, columns = ['open', 'high', 'low', 'close', 'volume']
                The latest time record at the bottom of the dateFrame.
        """
        self._log.debug(__name__ + '::get_historical_data: security=%s barSize=%s goBack=%s endTime=%s whatToShow=%s useRTH=%s waitForFeedbackInSeconds=%s' % (security, barSize, goBack, endTime, whatToShow, useRTH, waitForFeedbackInSeconds))

        # all request datetime MUST be switched to UTC then submit to IB
        if endTime is not None and endTime != '':
            if endTime.tzinfo is None:
                self._log.error(__name__ + '::request_historical_data: EXIT, endTime=%s must have timezone' % (endTime,))
                exit()
            endTime = endTime.astimezone(tz=pytz.utc)
            endTime = dt.datetime.strftime(endTime, "%Y%m%d %H:%M:%S %Z")  # datetime -> string
        if whatToShow == '':
            whatToShow = choose_whatToShow(security.secType)
        orderIdList = self.submit_requests(ReqHistoricalData(security, barSize, goBack, endTime, whatToShow, useRTH, waitForFeedbackInSeconds, followUp=followUp))
        return self._brokerClient.get_submit_requests_result(orderIdList[0])  # return a pandas dataFrame

    def get_order(self, ibpyOrderId):
        """

        :param ibpyOrderId: string
        :return: broker_factory::records_def::IBridgePyOrder
        """
        raise NotImplementedError(self.name)

    def get_position(self, accountCode, security):
        raise NotImplementedError(self.name)

    def get_real_time_price(self, security, tickType, followUp=True):
        raise NotImplementedError(self.name)

    def get_5_second_real_time_bar(self, security, tickType, followUp=True):
        raise NotImplementedError(self.name)

    def get_timestamp(self, security, tickType):
        raise NotImplementedError(__name__ + '::get_timestamp: %s' % (self.name,))

    def get_real_time_size(self, security, tickType, followUp=True):
        raise NotImplementedError(self.name)

    def order_status_monitor(self, ibpyOrderId, target_status, waitingTimeInSeconds=30):
        raise NotImplementedError(self.name)

    def get_option_info(self, security, fields, waitForFeedbackInSeconds=30):
        self._log.debug(__name__ + '::get_option_info: security=%s fields=%s' % (security.full_print(), str(fields)))
        # if the request of real time price is not already submitted
        # submit_requests guarantee valid ask_price and valid bid_price
        if not self._brokerClient.is_real_time_price_requested(security):
            self.submit_requests(ReqMktData(security, waitForFeedbackInSeconds=waitForFeedbackInSeconds))
        ans = {}
        for fieldName in fields:
            if fieldName in ['delta', 'gamma', 'vega', 'theta', 'impliedVol', 'optPrice', 'undPrice']:
                ans[fieldName] = self._dataFromServer.get_value(security, IBCpp.TickType.LAST_OPTION_COMPUTATION, fieldName)
            elif fieldName in ['option_call_open_interest']:
                ans[fieldName] = self._dataFromServer.get_value(security, IBCpp.TickType.OPTION_CALL_OPEN_INTEREST, 'size')
            elif fieldName in ['option_put_open_interest']:
                ans[fieldName] = self._dataFromServer.get_value(security, IBCpp.TickType.OPTION_PUT_OPEN_INTEREST, 'size')
            else:
                exit(__name__ + '::get_option_info: EXIT, cannot handle security=%s fieldName=%s' % (security.full_print(), fieldName))
        return ans

    def place_order(self, ibridgePyOrder, followUp=True, waitForFeedbackInSeconds=30):
        self._log.debug(__name__ + '::place_order: ibridgePyOrder=%s' % (ibridgePyOrder,))
        contract = ibridgePyOrder.requestedContract
        order = ibridgePyOrder.requestedOrder
        if Decimal(order['totalQuantity']) != 0:
            reqIdList = self.submit_requests(PlaceOrder(contract=contract, order=order, followUp=followUp, waitForFeedbackInSeconds=waitForFeedbackInSeconds))
            return self._brokerClient.get_submit_requests_result(reqIdList[0])  # return ibpyOrderId
        else:
            self._log.info('No order was placed because order.totalQuantity = 0.')
            return 'NoOrderPlaced'

    def processMessages(self, timeNow):
        # self._log.info(f'{__name__}::processMessages: id(self._brokerClient)={id(self._brokerClient)}')
        return self._brokerClient.processMessagesWrapper(timeNow)

    def submit_requests(self, *args):
        """

        :param args: broker_client_factory::BrokerClientDefs::Request
        :return: a list of reqId !!!
        """
        self._log.notset(f'{__name__}::submit_requests: args={args}')
        return self._brokerClient.request_data(*args)

    def use_next_id(self):
        return self._brokerClient.use_next_id()
