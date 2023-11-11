# coding=utf-8
import datetime as dt
import math
import time
from sys import exit

import pandas as pd
import pytz
from decimal import Decimal

from BasicPyLib.BasicTools import roundToMinTick
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.IbridgepyTools import special_match, create_order, check_same_security, from_symbol_to_security, \
    print_decisions, symbol
from IBridgePy.constants import OrderStatus, FollowUpRequest, OrderType, OrderTif, DataProviderName
from IBridgePy.quantopian import QDataClass
from IBridgePy.quantopian import Security
from IBridgePy.quantopian import TimeBasedRules, calendars, from_contract_to_security
from IBridgePy.OrderTypes import MarketOrder, StopOrder, LimitOrder
from IBridgePy.trader_defs import Context
from broker_client_factory.BrokerClientDefs import ReqIds, ReqAccountSummary, ReqAccountUpdates, ReqAllOpenOrders, \
    ReqCurrentTime, ReqPositions, ModifyOrder
# https://www.interactivebrokers.com/en/software/api/apiguide/tables/tick_types.htm
from broker_client_factory.CustomErrors import NotEnoughFund
from models.Order import IbridgePyOrder
from tools.hist_converter import convert_hist_using_epoch_to_timestamp

TICK_TYPE_MAPPER = {
    'ask_price': IBCpp.TickType.ASK,
    'bid_price': IBCpp.TickType.BID,
    'last_price': IBCpp.TickType.LAST,
    'price': IBCpp.TickType.LAST,
    'open': IBCpp.TickType.OPEN,
    'high': IBCpp.TickType.HIGH,
    'low': IBCpp.TickType.LOW,
    'close': IBCpp.TickType.CLOSE,
    'volume': IBCpp.TickType.VOLUME,
    'ask_size': IBCpp.TickType.ASK_SIZE,
    'bid_size': IBCpp.TickType.BID_SIZE,
    'last_size': IBCpp.TickType.LAST_SIZE,
    'ask_option_computation': IBCpp.TickType.ASK_OPTION_COMPUTATION,
    'bid_option_computation': IBCpp.TickType.BID_OPTION_COMPUTATION,
    'last_option_computation': IBCpp.TickType.LAST_OPTION_COMPUTATION,
    'model_option': IBCpp.TickType.MODEL_OPTION,
    'option_call_open_interest': IBCpp.TickType.OPTION_CALL_OPEN_INTEREST,
    'option_put_open_interest': IBCpp.TickType.OPTION_PUT_OPEN_INTEREST
}


def _get_same_security_from_list(aSecurity, aList):
    for security in aList:
        if check_same_security(aSecurity, security):
            return security
    return None


def _is_in_security_list(a_security, ls_security):
    for sec in ls_security:
        if check_same_security(sec, a_security):
            return True
    return False


def calculate_target_share_under_commission(portfolio_value, target_percent, current_price, current_share, comm_func):
    new_share = int(portfolio_value * target_percent / current_price)
    while True:
        new_holding_amount = new_share * current_price
        trading_share = abs(Decimal(new_share) - Decimal(current_share))
        if Decimal(new_holding_amount) / (Decimal(portfolio_value) - Decimal(comm_func(float(trading_share)))) <= target_percent:
            # print(f'calculate_target_share_under_commission: portfolio_value={portfolio_value} target_percent={target_percent} current_price={current_price} current_share={current_share} ans={new_share}')
            return str(new_share)
        else:
            new_share -= 1


class Trader(object):
    # In run_like_quantopian mode, at the beginning of a day, run code to check if
    # scheduled_functions should run on that day. This is the flag. It will be saved for the whole day.
    runScheduledFunctionsToday = True

    # MarketMangerBase will monitor it to stop
    # False is want to run
    wantToEnd = False

    scheduledFunctionList = []  # record all of singleTrader scheduled function conditions

    # a list of accountCodes called back from IB server
    # singleTrader's input accountCode will be checked against this list
    accountCodeCallBackList = None

    accountCodeSet = None
    multiAccountFlag = None

    def __init__(self):
        self._userConfig = None
        # settings from user
        self._fileName = None
        self._logLevel = None
        self._accountCode = None

        # settings from setting.py
        self._sysTimeZone = None
        self._showTimeZone = None
        self._runScheduledFunctionBeforeHandleData = None
        self._multiAccSummaryTag = None

        # user's input by loading user's fileName
        self.initialize_quantopian = None
        self.handle_data_quantopian = None
        self.before_trading_start_quantopian = None

        # userLog is for the function of record (). User will use it for any reason.
        # They should be passed in from userConfig
        self._userLog = None
        self._log = None

        self._marketCalendar = None
        self._emailClient = None
        self._brokerService = None
        self._dataProviderService = None
        self._dataProviderFactory = None  # temp solution to get hist from yahoo finance
        self.tick_type_mapper = TICK_TYPE_MAPPER

        # Other internal variables
        self.context = None
        self.qData = None

        self._simulate_commission = None

    def __str__(self):
        return '{brokerService=%s dataProviderService=%s id=%s}' % (self._brokerService, self._dataProviderService, id(self))

    def update_from_userConfig(self, userConfig):
        self._userConfig = userConfig
        self._fileName = userConfig.projectConfig.fileName
        # In the run_like_quantopian mode
        # the system should use Easter timezone as the system time
        # self.sysTimeZone will be used for this purpose
        # schedule_function will use this to run schedules
        # Repeater will use this to run schedules as well
        self._sysTimeZone = userConfig.projectConfig.sysTimeZone

        self._showTimeZone = userConfig.projectConfig.showTimeZone
        self._multiAccSummaryTag = userConfig.projectConfig.multiAccountSummaryTag
        self._log = userConfig.log
        self._userLog = userConfig.userLog
        self._emailClient = userConfig.emailClient
        self._marketCalendar = userConfig.marketCalendar
        self._brokerService = userConfig.brokerService
        self._dataProviderService = userConfig.dataProviderService
        self._dataProviderFactory = userConfig.dataProviderFactory
        self._accountCode = userConfig.projectConfig.accountCode
        self.initialize_quantopian = userConfig.initialize_quantopian
        self.handle_data_quantopian = userConfig.handle_data_quantopian
        self.before_trading_start_quantopian = userConfig.before_trading_start_quantopian

        self._runScheduledFunctionBeforeHandleData = userConfig.projectConfig.runScheduledFunctionBeforeHandleData
        self._simulate_commission = self._userConfig.backtesterConfig.simulateCommission

        if isinstance(self._accountCode, list) or isinstance(self._accountCode, set) or isinstance(self._accountCode, tuple):
            self.multiAccountFlag = True
            self.accountCodeSet = set(self._accountCode)
        else:
            self.multiAccountFlag = False
            self.accountCodeSet = {self._accountCode}  # change from string to set

        # set up context and qData.data
        self.context = Context(self, self.accountCodeSet)
        self.qData = QDataClass(self)
        if self._accountCode == '':
            self._log.error('EXIT, do not forget to change accountCode in userConfig')
            exit()

    @property
    def versionNumber(self):
        return self._brokerService.versionNumber

    def terminate_all_clients(self):
        self._userConfig.brokerClientFactory.disconnect_all_client()

    def getBrokerService(self):
        return self._brokerService

    def getLog(self):
        return self._log

    def getWantToEnd(self, dummyTimeNow=None):
        """
        The function is used in Repeater in MarketManagerBase.py to know if repeat should stop
        dummy input = because it can be program to stop based on an input datetime
        :return: bool
        """
        self._log.notset(__name__ + '::getWantToEnd: dummyTimeNow=%s' % (dummyTimeNow,))
        return self.wantToEnd

    def setWantToEnd(self):
        self.wantToEnd = True
        self.disconnect()

    def adjust_accountCode(self, accountCode):
        if accountCode == 'default':
            if not self.multiAccountFlag:
                return self._accountCode
            else:
                self._log.error(__name__ + '::adjust_accountCode: EXIT, Must specify an accountCode')
                exit()
        else:
            if not self.multiAccountFlag:
                if accountCode in self.accountCodeSet:
                    return accountCode
                else:
                    self._log.error(
                        __name__ + '::adjust_accountCode: EXIT, wrong input accountCode=%s accountCodeSet=%s' % (
                            accountCode, str(self.accountCodeSet)))
                    exit()
            else:
                if accountCode in self.accountCodeSet:
                    return accountCode
                else:
                    self._log.error(
                        __name__ + '::adjust_accountCode: EXIT, wrong user input, accountCode=%s does not exist in Multi account codes=%s' % (
                            accountCode, self.accountCodeSet))
                    exit()

    def get_ibpy_expiry_in_days(self):
        """

        :return: int, number of days of IBridgePy passcode to expiry
        """
        return self._brokerService.get_ibpy_expiry_in_days()

    def get_TD_access_token_expiry_in_days(self):
        # Depends on the user's input from setting.py BROKER_CLIENT -> TD_CLIENT -> refreshTokenCreatedOn
        return self._brokerService.get_TD_access_token_expiry_in_days()

    def get_new_TD_refresh_token(self):
        return self._brokerService.get_new_TD_refresh_token()

    def connect(self):
        return self._brokerService.connect()

    def disconnect(self):
        self._log.debug(f"{__name__}::disconnect: ")
        self._brokerService.disconnect()

    def get_next_time(self):
        timeNow = self._brokerService.get_next_time().astimezone(self._sysTimeZone)
        self._log.notset(__name__ + '::get_next_time: timeNow=%s' % (timeNow,))
        return timeNow

    # noinspection PyUnusedLocal
    def get_heart_beats(self, dummy):
        """
        Trigger heart beats request to IB server
        :param dummy: to be scheduled by BasicPyLib.repeater.Event, it mush have one input.
        :return:
        """
        self._brokerService.get_heart_beats()

    def count_positions(self, security, accountCode='default'):
        self._log.debug(__name__ + '::count_positions:security=%s' % (security.full_print(),))
        adj_accountCode = self.adjust_accountCode(accountCode)
        positionRecord = self.get_position(security, adj_accountCode)
        return positionRecord.amount

    def close_all_positions(self, orderStatusMonitor=True, accountCode='default'):
        self._log.debug(__name__ + '::close_all_positions:')
        adj_accountCode = self.adjust_accountCode(accountCode)
        positions = self.get_all_positions(adj_accountCode)  # return a dictionary
        orderIdList = []

        # !!! cannot iterate positions directly because positions can change during the iteration if any orders are
        # executed.
        # The solution is to use another list to record all security to be closed.
        adj_securities = list(positions.keys())

        # place close orders
        for security in adj_securities:
            ibpyOrderId = self.order_target(security, 0, accountCode=adj_accountCode)
            orderIdList.append(ibpyOrderId)

        # Monitor status
        if orderStatusMonitor:
            for ibpyOrderId in orderIdList:
                self.order_status_monitor(ibpyOrderId, OrderStatus.FILLED)

    def close_all_positions_except(self, ls_security, orderStatusMonitor=True, accountCode='default'):
        # self._log.debug(__name__ + '::close_all_positions_except:' + str(a_security))
        adj_accountCode = self.adjust_accountCode(accountCode)
        orderIdList = []
        for security in self.get_all_positions(adj_accountCode):
            if not _is_in_security_list(security, ls_security):
                ibpyOrderId = self.order_target(security, 0, accountCode=adj_accountCode)
                orderIdList.append(ibpyOrderId)
        if orderStatusMonitor:
            for ibpyOrderId in orderIdList:
                self.order_status_monitor(ibpyOrderId, OrderStatus.FILLED)

    def cancel_all_orders(self, accountCode='default'):
        self._log.debug(__name__ + '::cancel_all_orders')
        """
        TODO: cancel_all_orders is not batch requestRecord. If any cancel-request fails, the code will terminate. 
        Maybe change it to batch requestRecord.
        """
        adj_accountCode = self.adjust_accountCode(accountCode)
        orders = self._brokerService.get_all_orders(adj_accountCode)
        for ibpyOrderId in orders:
            if orders[ibpyOrderId].status not in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.INACTIVE, OrderStatus.PENDINGCANCEL]:
                self.cancel_order(ibpyOrderId)

    def get_contract_details(self, secType, symbol, field, currency='USD', exchange='', primaryExchange='', expiry='',
                             strike=0.0, right='', multiplier='', localSymbol='', waitForFeedbackInSeconds=30):
        security = Security(secType=secType, symbol=symbol, currency=currency, exchange=exchange,
                            primaryExchange=primaryExchange, expiry=expiry, strike=strike, right=right,
                            multiplier=multiplier, localSymbol=localSymbol)
        return self._brokerService.get_contract_details(security, field, waitForFeedbackInSeconds=waitForFeedbackInSeconds)

    def get_scanner_results(self, waitForFeedbackInSeconds=30, **kwargs):
        return self._brokerService.get_scanner_results(waitForFeedbackInSeconds, kwargs)

    def get_option_info(self, security, fields, waitForFeedbackInSeconds=30):
        self._log.debug(__name__ + '::get_option_greeks: security=%s fields=%s waitForFeedbackInSecond=%s' % (security.full_print(), fields, waitForFeedbackInSeconds))
        self._brokerService.add_exchange_primaryExchange_to_security(security)
        return self._brokerService.get_option_info(security, fields, waitForFeedbackInSeconds=waitForFeedbackInSeconds)

    def processMessages(self, timeNow):
        """
        this function is created to fit the new RepeaterEngine because any functions to be scheduled must have two input
        times. It is easier to input two times to repeated function(?)
        :param timeNow:
        :return:
        """
        self._log.notset(__name__ + '::processMessages: timeNow=%s' % (str(timeNow),))
        self._brokerService.processMessages(timeNow)

    def _validate_input_accountCode(self, accountCode):
        self._log.debug(__name__ + '::_validate_input_accountCode: accountCode=%s' % (accountCode,))
        accountCodeCallBackList = self._brokerService.get_active_accountCodes()
        if accountCode in accountCodeCallBackList:
            return
        else:
            self._log.error(__name__ + '::_validate_input_accountCode: EXIT, accountCode=%s is not acceptable' % (accountCode,))
            self._log.error(__name__ + f'::_validate_input_accountCode: possible accountCodes are {accountCodeCallBackList}')
            exit()

    def get_datetime(self, timezone='default'):
        """
        Get the current datetime of IB system similar to that defined in Quantopian
        :param timezone: str, representing timezone defined by pytz, for example, 'US/Pacific' and 'US/Eastern'
        :return: a zoned python DateTime
        """
        timeNow = self._brokerService.get_datetime()
        if timezone == 'default':
            ans = timeNow.astimezone(self._showTimeZone)
        else:
            ans = timeNow.astimezone(pytz.timezone(timezone))
        self._log.notset(__name__ + '::get_datetime: timeNow=%s' % (timeNow,))
        return ans

    def initialize_Function(self):
        self._log.debug(__name__ + '::initialize_Function')
        self._log.info('IBridgePy version %s' % (self.versionNumber,))
        self._log.info('fileName = %s' % (self._fileName,))

        self._brokerService.submit_requests(ReqIds())
        self._brokerService.submit_requests(ReqCurrentTime())
        if self.multiAccountFlag:
            self._brokerService.submit_requests(
                ReqAccountSummary(tag=self._multiAccSummaryTag),
                ReqAllOpenOrders(),
                ReqPositions())
        else:
            self._brokerService.submit_requests(
                ReqAccountUpdates(True, self._accountCode),
                ReqAllOpenOrders(),
                ReqPositions())

        # self.accountCodeCallBackList = self._brokerService.get_active_accountCodes()

        self._log.debug(__name__ + '::initialize_Function::start to run customers init function')
        self.initialize_quantopian(self.context)  # function name was passed in.

        self._log.info('####    Starting to initialize trader    ####')
        if self.multiAccountFlag:
            for acctCode in self.accountCodeSet:
                self._validate_input_accountCode(acctCode)
                self.display_all(acctCode)
        else:
            self._validate_input_accountCode(self._accountCode)
            self.display_all()

        # DO NOT DELETE
        # to debug schedule_function()
        # print(__name__ + '::initialize_Function: printing scheduledFunctionList')
        # for ct in self.scheduledFunctionList:
        #     print(ct)

        self._log.info('####    Initialize trader COMPLETED    ####')

    def repeat_Function(self, dummyTime):
        """Must have one parameter to be scheduled in IBridgePy repeater"""
        self._log.notset(__name__ + '::repeat_Function: dummyTime=%s' % (dummyTime,))
        # TODO: it is better off to set self.runScheduledFunctionsToday every day to save time for simulation
        if self.runScheduledFunctionsToday:
            if self._runScheduledFunctionBeforeHandleData:
                self._check_schedules()

        self.handle_data_quantopian(self.context, self.qData)

        if self.runScheduledFunctionsToday:
            if not self._runScheduledFunctionBeforeHandleData:
                self._check_schedules()

    def before_trade_start_Function(self, dummyTime):
        """Must have one parameter to be scheduled in IBridgePy repeater"""
        self._log.debug(__name__ + '::before_trade_start_Function: dummyTime=%s' % (str(dummyTime),))
        self.before_trading_start_quantopian(self.context, self.qData)

    def display_positions(self, accountCode='default'):
        self._log.notset(__name__ + '::display_positions: accountCode=%s' % (accountCode,))
        adj_accountCode = self.adjust_accountCode(accountCode)
        positions = self.get_all_positions(adj_accountCode)  # return a dictionary

        if len(positions) == 0:
            self._log.info('##    NO ANY POSITION    ##')
        else:
            self._log.info('##    POSITIONS %s   ##' % (adj_accountCode,))
            self._log.info('Symbol Amount Cost_basis')

            for security in positions:
                a = positions[security].str_security
                b = positions[security].amount
                c = positions[security].cost_basis
                self._log.info(str(a) + ' ' + str(b) + ' ' + str(c))

    def display_orderStatus(self, accountCode='default'):
        self._log.notset(__name__ + '::display_orderStatus: accountCode=%s' % (accountCode,))
        adj_accountCode = self.adjust_accountCode(accountCode)
        orders = self._brokerService.get_all_orders(adj_accountCode)

        if len(orders) >= 1:
            self._log.info('##    Order Status %s   ##' % (adj_accountCode,))
            for ibpyOrderId in orders:
                self._log.info(str(orders[ibpyOrderId]))
            self._log.info('##    END    ##')
        else:
            self._log.info('##    NO any order    ##')

    def display_account_info(self, accountCode='default'):
        """
        display account info such as position values in format ways
        """
        self._log.notset(__name__ + '::display_account_info: accountCode=%s' % (accountCode,))
        adj_accountCode = self.adjust_accountCode(accountCode)
        self._log.info('##    ACCOUNT Balance  %s  ##' % (adj_accountCode,))
        a = self._brokerService.get_account_info(adj_accountCode, 'TotalCashValue')
        b = self._brokerService.get_account_info(adj_accountCode, 'NetLiquidation')
        c = self._brokerService.get_account_info(adj_accountCode, 'GrossPositionValue')
        # d = self.brokerService.get_account_info(adj_accountCode, 'AvailableFunds')  # backtester is not ready 20200819
        self._log.info('CASH=%s' % (a,))
        self._log.info('portfolio_value=%s' % (b,))
        self._log.info('positions_value=%s' % (c,))
        # self._log.info('available_funds=%s' % (d,))

        if a + b + c < 0.0:
            self._log.error(__name__ + '::display_account_info: EXIT, Wrong input accountCode = %s'
                            % (self._accountCode,))
            # self.accountCodeCallBackSet.discard(self.accountCode)
            # self.accountCodeCallBackSet.discard('default')
            # if len(self.accountCodeCallBackSet):
            #     self._log.error(__name__ + '::display_account_info: Possible accountCode = %s'
            #                    % (' '.join(self.accountCodeCallBackSet)))
            exit()

    def display_all(self, accountCode='default'):
        self._log.debug(__name__ + '::display_all: accountCode=%s' % (accountCode,))
        accountCode = self.adjust_accountCode(accountCode)
        self.display_account_info(accountCode)
        self.display_positions(accountCode)
        self.display_orderStatus(accountCode)

    def _get_portfolio(self, accountCode):
        self._log.notset(__name__ + '::_get_portfolio: accountCode=%s' % (accountCode,))
        adj_accountCode = self.adjust_accountCode(accountCode)
        return self.context.portfolioQ[adj_accountCode]

    def show_account_info(self, field, meta='value', accountCode='default'):
        """
        :param field: string or list of string of the following field names. IB and TD may not have the same fields available.
                        Quantopian values of portfolio_value, cash, position_value are accepted. here.
        :param meta: NotImplemented 20200819. string. Option=['value', 'currency']. Other than "value", IB will callback currency. See broker_client_factory::CallBacks::updateAccountValue
        :param accountCode:
        :return: float or string depending on field name

        TD Ameritrade: NetLiquidation, GrossPositionValue, TotalCashValue, BuyingPower, AvailableFunds
        All of the following fields defined by IB can be used for this method
        https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html#ae15a34084d9f26f279abd0bdeab1b9b5
        AccountCode — The account ID number
        AccountOrGroup — "All" to return account summary data for all accounts, or set to a specific Advisor Account Group name that has already been created in TWS Global Configuration
        AccountReady — For internal use only
        AccountType — Identifies the IB account structure
        AccruedCash — Total accrued cash value of stock, commodities and securities
        AccruedCash-C — Reflects the current's month accrued debit and credit interest to date, updated daily in commodity segment
        AccruedCash-S — Reflects the current's month accrued debit and credit interest to date, updated daily in security segment
        AccruedDividend — Total portfolio value of dividends accrued
        AccruedDividend-C — Dividends accrued but not paid in commodity segment
        AccruedDividend-S — Dividends accrued but not paid in security segment
        AvailableFunds — This value tells what you have available for trading
        AvailableFunds-C — Net Liquidation Value - Initial Margin
        AvailableFunds-S — Equity with Loan Value - Initial Margin
        Billable — Total portfolio value of treasury bills
        Billable-C — Value of treasury bills in commodity segment
        Billable-S — Value of treasury bills in security segment
        BuyingPower — Cash Account: Minimum (Equity with Loan Value, Previous Day Equity with Loan Value)-Initial Margin, Standard Margin Account: Minimum (Equity with Loan Value, Previous Day Equity with Loan Value) - Initial Margin *4
        CashBalance — Cash recognized at the time of trade + futures PNL
        CorporateBondValue — Value of non-Government bonds such as corporate bonds and municipal bonds
        Currency — Open positions are grouped by currency
        Cushion — Excess liquidity as a percentage of net liquidation value
        DayTradesRemaining — Number of Open/Close trades one could do before Pattern Day Trading is detected
        DayTradesRemainingT+1 — Number of Open/Close trades one could do tomorrow before Pattern Day Trading is detected
        DayTradesRemainingT+2 — Number of Open/Close trades one could do two days from today before Pattern Day Trading is detected
        DayTradesRemainingT+3 — Number of Open/Close trades one could do three days from today before Pattern Day Trading is detected
        DayTradesRemainingT+4 — Number of Open/Close trades one could do four days from today before Pattern Day Trading is detected
        EquityWithLoanValue — Forms the basis for determining whether a client has the necessary assets to either initiate or maintain security positions
        EquityWithLoanValue-C — Cash account: Total cash value + commodities option value - futures maintenance margin requirement + minimum (0, futures PNL) Margin account: Total cash value + commodities option value - futures maintenance margin requirement
        EquityWithLoanValue-S — Cash account: Settled Cash Margin Account: Total cash value + stock value + bond value + (non-U.S. & Canada securities options value)
        ExcessLiquidity — This value shows your margin cushion, before liquidation
        ExcessLiquidity-C — Equity with Loan Value - Maintenance Margin
        ExcessLiquidity-S — Net Liquidation Value - Maintenance Margin
        ExchangeRate — The exchange rate of the currency to your base currency
        FullAvailableFunds — Available funds of whole portfolio with no discounts or intraday credits
        FullAvailableFunds-C — Net Liquidation Value - Full Initial Margin
        FullAvailableFunds-S — Equity with Loan Value - Full Initial Margin
        FullExcessLiquidity — Excess liquidity of whole portfolio with no discounts or intraday credits
        FullExcessLiquidity-C — Net Liquidation Value - Full Maintenance Margin
        FullExcessLiquidity-S — Equity with Loan Value - Full Maintenance Margin
        FullInitMarginReq — Initial Margin of whole portfolio with no discounts or intraday credits
        FullInitMarginReq-C — Initial Margin of commodity segment's portfolio with no discounts or intraday credits
        FullInitMarginReq-S — Initial Margin of security segment's portfolio with no discounts or intraday credits
        FullMaintMarginReq — Maintenance Margin of whole portfolio with no discounts or intraday credits
        FullMaintMarginReq-C — Maintenance Margin of commodity segment's portfolio with no discounts or intraday credits
        FullMaintMarginReq-S — Maintenance Margin of security segment's portfolio with no discounts or intraday credits
        FundValue — Value of funds value (money market funds + mutual funds)
        FutureOptionValue — Real-time market-to-market value of futures options
        FuturesPNL — Real-time changes in futures value since last settlement
        FxCashBalance — Cash balance in related IB-UKL account
        GrossPositionValue — Gross Position Value in securities segment
        GrossPositionValue-S — Long Stock Value + Short Stock Value + Long Option Value + Short Option Value
        IndianStockHaircut — Margin rule for IB-IN accounts
        InitMarginReq — Initial Margin requirement of whole portfolio
        InitMarginReq-C — Initial Margin of the commodity segment in base currency
        InitMarginReq-S — Initial Margin of the security segment in base currency
        IssuerOptionValue — Real-time mark-to-market value of Issued Option
        Leverage-S — GrossPositionValue / NetLiquidation in security segment
        LookAheadNextChange — Time when look-ahead values take effect
        LookAheadAvailableFunds — This value reflects your available funds at the next margin change
        LookAheadAvailableFunds-C — Net Liquidation Value - look ahead Initial Margin
        LookAheadAvailableFunds-S — Equity with Loan Value - look ahead Initial Margin
        LookAheadExcessLiquidity — This value reflects your excess liquidity at the next margin change
        LookAheadExcessLiquidity-C — Net Liquidation Value - look ahead Maintenance Margin
        LookAheadExcessLiquidity-S — Equity with Loan Value - look ahead Maintenance Margin
        LookAheadInitMarginReq — Initial margin requirement of whole portfolio as of next period's margin change
        LookAheadInitMarginReq-C — Initial margin requirement as of next period's margin change in the base currency of the account
        LookAheadInitMarginReq-S — Initial margin requirement as of next period's margin change in the base currency of the account
        LookAheadMaintMarginReq — Maintenance margin requirement of whole portfolio as of next period's margin change
        LookAheadMaintMarginReq-C — Maintenance margin requirement as of next period's margin change in the base currency of the account
        LookAheadMaintMarginReq-S — Maintenance margin requirement as of next period's margin change in the base currency of the account
        MaintMarginReq — Maintenance Margin requirement of whole portfolio
        MaintMarginReq-C — Maintenance Margin for the commodity segment
        MaintMarginReq-S — Maintenance Margin for the security segment
        MoneyMarketFundValue — Market value of money market funds excluding mutual funds
        MutualFundValue — Market value of mutual funds excluding money market funds
        NetDividend — The sum of the Dividend Payable/Receivable Values for the securities and commodities segments of the account
        NetLiquidation — The basis for determining the price of the assets in your account
        NetLiquidation-C — Total cash value + futures PNL + commodities options value
        NetLiquidation-S — Total cash value + stock value + securities options value + bond value
        NetLiquidationByCurrency — Net liquidation for individual currencies
        OptionMarketValue — Real-time mark-to-market value of options
        PASharesValue — Personal Account shares value of whole portfolio
        PASharesValue-C — Personal Account shares value in commodity segment
        PASharesValue-S — Personal Account shares value in security segment
        PostExpirationExcess — Total projected "at expiration" excess liquidity
        PostExpirationExcess-C — Provides a projected "at expiration" excess liquidity based on the soon-to expire contracts in your portfolio in commodity segment
        PostExpirationExcess-S — Provides a projected "at expiration" excess liquidity based on the soon-to expire contracts in your portfolio in security segment
        PostExpirationMargin — Total projected "at expiration" margin
        PostExpirationMargin-C — Provides a projected "at expiration" margin value based on the soon-to expire contracts in your portfolio in commodity segment
        PostExpirationMargin-S — Provides a projected "at expiration" margin value based on the soon-to expire contracts in your portfolio in security segment
        PreviousDayEquityWithLoanValue — Marginable Equity with Loan value as of 16:00 ET the previous day in securities segment
        PreviousDayEquityWithLoanValue-S — IMarginable Equity with Loan value as of 16:00 ET the previous day
        RealCurrency — Open positions are grouped by currency
        RealizedPnL — Shows your profit on closed positions, which is the difference between your entry execution cost and exit execution costs, or (execution price + commissions to open the positions) - (execution price + commissions to close the position)
        RegTEquity — Regulation T equity for universal account
        RegTEquity-S — Regulation T equity for security segment
        RegTMargin — Regulation T margin for universal account
        RegTMargin-S — Regulation T margin for security segment
        SMA — Line of credit created when the market value of securities in a Regulation T account increase in value
        SMA-S — Regulation T Special Memorandum Account balance for security segment
        SegmentTitle — Account segment name
        StockMarketValue — Real-time mark-to-market value of stock
        TBondValue — Value of treasury bonds
        TBillValue — Value of treasury bills
        TotalCashBalance — Total Cash Balance including Future PNL
        TotalCashValue — Total cash value of stock, commodities and securities
        TotalCashValue-C — CashBalance in commodity segment
        TotalCashValue-S — CashBalance in security segment
        TradingType-S — Account Type
        UnrealizedPnL — The difference between the current market value of your open positions and the average cost, or Value - Average Cost
        WarrantValue — Value of warrants
        WhatIfPMEnabled — To check projected margin requirements under Portfolio Margin model
        """
        self._log.debug(__name__ + '::show_account_info: field=%s accountCode=%s' % (field, accountCode))
        adj_accountCode = self.adjust_accountCode(accountCode)
        if field == 'portfolio_value':
            field = 'NetLiquidation'
        elif field == 'positions_value':
            field = 'GrossPositionValue'
        elif field == 'cash':
            field = 'TotalCashValue'
        ans = self._brokerService.get_account_info(adj_accountCode, field, meta)
        if ans is not None:  # ans could be real 0.0 or 0 for a real account situation
            return ans
        self._log.error(__name__ + '::show_account_info: EXIT, field=%s is not accessible accountCode=%s' % (field, accountCode))
        exit()

    def hold_any_position(self, accountCode='default'):
        self._log.debug(__name__ + '::hold_any_position')
        adj_accountCode = self.adjust_accountCode(accountCode)
        return len(self._brokerService.get_all_positions(adj_accountCode)) != 0

    def request_historical_data(self, security, barSize, goBack, endTime='', whatToShow='', useRTH=1,
                                waitForFeedbackInSeconds=30, timezoneOfReturn=pytz.timezone('US/Eastern'), dataProviderName=None, followUp=True):
        """

        :param followUp:
        :param dataProviderName: only works for DataProviderName.YAHOO
        :param security: Security
        :param barSize: string barSize can be any of the following values(string) 1 sec, 5 secs,15 secs,30 secs,1 min,2 mins,3 mins,5 mins,15 mins,30 mins,1 hour,1 day
        :param goBack: string
        :param endTime: default value is '', IB server deems '' as the current server time. If user wants to supply a value, it must be a datetime with timezone
        :param whatToShow: string See IB documentation for choices TRADES,MIDPOINT,BID,ASK,BID_ASK,HISTORICAL_VOLATILITY,OPTION_IMPLIED_VOLATILITY
        :param useRTH: int 1=within regular trading hours, 0=ignoring RTH
        :param waitForFeedbackInSeconds:
        :param timezoneOfReturn: the index of the returned DataFrame will be adjusted
        :return: a DataFrame, keyed by a datetime with timezone UTC, columns = ['open', 'high', 'low', 'close', 'volume'] The latest time record at the bottom of the dateFrame.
        """
        if dataProviderName == DataProviderName.YAHOO_FINANCE:
            dataProvider = self._dataProviderFactory.get_dataProvider_by_name(dataProviderName, self._userConfig)
            return dataProvider.provide_hist_from_a_true_dataProvider(security, self.get_datetime(), goBack, barSize, whatToShow, useRTH)

        # The format in which the incoming bars' date should be presented.
        # Note that for day bars, only yyyyMMdd format is available.
        if self._dataProviderService:
            self._dataProviderService.add_exchange_primaryExchange_to_security(security)
            hist = self._dataProviderService.get_historical_data(security, barSize, goBack, endTime, whatToShow, useRTH, waitForFeedbackInSeconds, followUp=followUp)
        else:
            self._brokerService.add_exchange_primaryExchange_to_security(security)
            hist = self._brokerService.get_historical_data(security, barSize, goBack, endTime, whatToShow, useRTH, waitForFeedbackInSeconds, followUp=followUp)
        if len(hist) == 0:
            self._log.info("There is no any historical data available from the Broker right now. Please double check the input parameters to the function of request_historical_data.")
            return pd.DataFrame()
        return convert_hist_using_epoch_to_timestamp(hist, timezoneOfReturn)

    def show_real_time_price(self, security, param, followUp=True):
        self._log.notset(__name__ + '::show_real_time_price: security=%s param=%s' % (security, param))
        # self.validator.showRealTimePriceValidator.validate(security, adj_param)
        self._dataProviderService.add_exchange_primaryExchange_to_security(security)
        return self._dataProviderService.get_real_time_price(security, self.tick_type_mapper[param], followUp)

    def show_timestamp(self, security, param):
        """
        Show the timestamp of a field of a security
        :param security: a security
        :param param: the field name
        :return: the timestamp when the IB callback happens
        """
        self._log.notset(__name__ + '::show_timestamp: security=%s param=%s' % (security, param))
        self._dataProviderService.add_exchange_primaryExchange_to_security(security)
        return self._dataProviderService.get_timestamp(security, self.tick_type_mapper[param])

    def show_real_time_size(self, security, param, followUp=True):
        self._log.notset(__name__ + '::show_real_time_size: security=%s param=%s' % (str(security), str(param)))
        self._dataProviderService.add_exchange_primaryExchange_to_security(security)
        return self._dataProviderService.get_real_time_size(security, self.tick_type_mapper[param], followUp=followUp)

    def cancel_order(self, ibpyOrderId):
        """
        function to cancel orders
        """
        if isinstance(ibpyOrderId, str):
            self._log.debug(__name__ + '::cancel_order: ibpyOrderId=%s' % (ibpyOrderId,))
            self._brokerService.cancel_order(ibpyOrderId)
        elif isinstance(ibpyOrderId, int):
            self._log.error(__name__ + '::cancel_order: ibpyOrderId must be a string')
            exit()
        elif isinstance(ibpyOrderId, IbridgePyOrder):
            self._log.debug(__name__ + '::cancel_order: ibpyOrderId=%s' % (ibpyOrderId.getIbpyOrderId(),))
            self._brokerService.cancel_order(ibpyOrderId.getIbpyOrderId())

    def create_order(self, action, amount, security, orderDetails, ocaGroup=None, ocaType=None, transmit=None,
                     parentId=None, orderRef='', outsideRth=False, hidden=False, accountCode='default'):
        int_orderId = self._brokerService.use_next_id()
        adj_accountCode = self.adjust_accountCode(accountCode)
        if action == 'BUY':
            amount = abs(amount)
        else:
            amount = -1 * abs(amount)
        self._brokerService.add_exchange_primaryExchange_to_security(security)
        ans = create_order(int_orderId, adj_accountCode, security, amount, orderDetails, self.get_datetime(),
                           ocaGroup=ocaGroup, ocaType=ocaType, transmit=transmit, parentId=parentId,
                           orderRef=orderRef, outsideRth=outsideRth, hidden=hidden)
        return ans

    def order(self, security, amount, style=MarketOrder(), orderRef='',
              accountCode='default', outsideRth=False, hidden=False, waitForFeedbackInSeconds=30, followUp=True):
        self._log.debug(__name__ + '''::order: security=%s amount=%s style=%s orderRef=%s accountCode=%s outsideRth=%s hidden=%s''' % (security.full_print(), amount, style, orderRef, accountCode, outsideRth, hidden))
        adj_accountCode = self.adjust_accountCode(accountCode)
        int_orderId = self._brokerService.use_next_id()
        self._brokerService.add_exchange_primaryExchange_to_security(security)
        ibridgePyOrder = create_order(int_orderId, adj_accountCode, security, amount, style, self.get_datetime(),
                                      orderRef=orderRef,
                                      outsideRth=outsideRth, hidden=hidden)
        return self._brokerService.place_order(ibridgePyOrder, followUp=followUp, waitForFeedbackInSeconds=waitForFeedbackInSeconds)

    def order_percent(self, security, percent, style=MarketOrder(), orderRef='', followUp=True,
                      accountCode='default'):
        self._log.notset(__name__ + '::order_percent')
        adj_accountCode = self.adjust_accountCode(accountCode)
        self._check_percent_validity(percent)
        portfolio_value = self._brokerService.get_account_info(adj_accountCode, 'NetLiquidation')
        current_price = self.show_real_time_price(security, 'ask_price')
        targetShare = calculate_target_share_under_commission(portfolio_value, percent, current_price, 0, self._simulate_commission)
        return self.order(security, amount=int(targetShare * percent), style=style,
                          orderRef=orderRef, accountCode=adj_accountCode, followUp=followUp)

    def _check_percent_validity(self, percent):
        if percent > 1.0 or percent < -1.0:
            self._log.error(f'order_percent: EXIT, percent={percent} outside the range of [-1.0, 1.0]')
            exit()

    def order_target(self, security, amount, style=MarketOrder(), orderRef='', followUp=True,
                     accountCode='default'):
        self._log.debug(__name__ + '::order_target: security=%s amount=%s' % (security.full_print(), amount))
        adj_accountCode = self.adjust_accountCode(accountCode)
        position = self.get_position(security, accountCode=adj_accountCode)
        hold = position.amount
        if amount != hold:
            # amount - hold is correct, confirmed
            return self.order(security, amount=str(Decimal(amount) - Decimal(hold)), style=style,
                              orderRef=orderRef, accountCode=adj_accountCode, followUp=followUp)
        else:
            self._log.debug(__name__ + '::order_target: %s No action is needed' % (security,))
            return 'NoOrderPlaced'

    def order_target_percent(self, security, percent, style=MarketOrder(), orderRef='', followUp=True,
                             accountCode='default'):
        adj_accountCode = self.adjust_accountCode(accountCode)
        self._check_percent_validity(percent)
        portfolio_value = self._brokerService.get_account_info(adj_accountCode, 'NetLiquidation')

        current_price = self.show_real_time_price(security, 'ask_price')
        current_share = self.count_positions(security)

        if math.isnan(current_price):
            self._log.error('order_target_percent: EXIT, No real time price is available right now. Market closed? real_time_price is NaN security=%s' % (security.full_print(),))
            exit()
        if current_price <= 0.0:
            self._log.error('order_target_percent: EXIT, No real time price is available right now. Market closed? real_time_price=%s security=%s' % (current_price, security.full_print()))
            exit()

        targetShare = calculate_target_share_under_commission(portfolio_value, percent, current_price, current_share, self._simulate_commission)

        # Keep to debug
        # cash_value = self._brokerService.get_account_info(adj_accountCode, 'TotalCashValue')
        # print(f'order_target_percent:: targetShare={targetShare} portfolio_value={portfolio_value} cash_value={cash_value} current_price={current_price}')

        return self.order_target(security, amount=targetShare, style=style,
                                 orderRef=orderRef, accountCode=adj_accountCode, followUp=followUp)

    def order_target_value(self, security, value, style=MarketOrder(), orderRef='', followUp=True,
                           accountCode='default'):
        self._log.notset(__name__ + '::order_target_value')
        adj_accountCode = self.adjust_accountCode(accountCode)
        targetShare = int(value / self.show_real_time_price(security, 'ask_price'))
        return self.order_target(security, amount=targetShare, style=style,
                                 orderRef=orderRef, accountCode=adj_accountCode, followUp=followUp)

    def order_value(self, security, value, style=MarketOrder(), orderRef='', followUp=True,
                    accountCode='default'):
        self._log.notset(__name__ + '::order_value')
        adj_accountCode = self.adjust_accountCode(accountCode)
        targetShare = int(value / self.show_real_time_price(security, 'ask_price'))
        return self.order(security, amount=targetShare, style=style,
                          orderRef=orderRef, accountCode=adj_accountCode, followUp=followUp)

    def _build_order_helper(self, security, amount, style=MarketOrder(), orderRef='', accountCode='default'):
        self._brokerService.add_exchange_primaryExchange_to_security(security)
        ocaGroup = str(dt.datetime.now())
        adj_accountCode = self.adjust_accountCode(accountCode)
        int_parentOrderId = self._brokerService.use_next_id()
        parentOrder = create_order(int_parentOrderId, adj_accountCode, security, amount, style, self.get_datetime(),
                                   ocaGroup=ocaGroup, orderRef=orderRef)
        int_slOrderId = self._brokerService.use_next_id()
        return adj_accountCode, parentOrder, int_slOrderId, ocaGroup, int_parentOrderId

    def place_order_with_stoploss(self, security, amount, stopLossPrice, style=MarketOrder(), tif='DAY', orderRef='',
                                  accountCode='default'):
        # https://developer.tdameritrade.com/content/place-order-samples Not implemented for TD yet
        adj_accountCode, parentOrder, int_slOrderId, ocaGroup, int_parentOrderId = self._build_order_helper(security, amount, style, orderRef, accountCode)
        slOrder = create_order(int_slOrderId, adj_accountCode, security, -amount, StopOrder(stopLossPrice, tif=tif),
                               self.get_datetime(), ocaGroup=ocaGroup, orderRef=orderRef)
        # IB recommends this way to place takeProfitOrder and stopLossOrder
        # with main order.
        parentOrder.requestedOrder['transmit'] = False
        slOrder.requestedOrder['parentId'] = int_parentOrderId
        slOrder.requestedOrder['transmit'] = True  # only transmit slOrder to avoid inadvertent actions

        # Does not follow up on place_order(parentOrder) because it is a partial order
        # As IB recommended, parentOrder and takeProfitOrder are not transmitted, so that IBridgePy should not follow up
        str_parentOrderId = self._brokerService.place_order(parentOrder, followUp=False)
        str_slOrderId = self._brokerService.place_order(slOrder)
        return str_parentOrderId, str_slOrderId

    def place_order_with_takeprofit(self, security, amount, takeProfitPrice, style=MarketOrder(), tif='DAY', orderRef='',
                                    accountCode='default'):
        # https://developer.tdameritrade.com/content/place-order-samples Not implemented for TD yet
        adj_accountCode, parentOrder, int_tpOrderId, ocaGroup, int_parentOrderId = self._build_order_helper(security, amount, style, orderRef, accountCode)
        tpOrder = create_order(int_tpOrderId, adj_accountCode, security, -amount, LimitOrder(takeProfitPrice, tif=tif),
                               self.get_datetime(), ocaGroup=ocaGroup, orderRef=orderRef)
        # IB recommends this way to place takeProfitOrder and stopLossOrder
        # with main order.
        parentOrder.requestedOrder['transmit'] = False
        tpOrder.requestedOrder['parentId'] = int_parentOrderId
        tpOrder.requestedOrder['transmit'] = True
        # Does not follow up on place_order(parentOrder) because it is a partial order
        # As IB recommended, parentOrder and takeProfitOrder are not transmitted, so that IBridgePy should not follow up
        str_parentOrderId = self._brokerService.place_order(parentOrder, followUp=False)
        str_tpOrderId = self._brokerService.place_order(tpOrder)
        return str_parentOrderId, str_tpOrderId

    # noinspection DuplicatedCode
    def place_order_with_stoploss_takeprofit(self, security, amount, stopLossPrice, takeProfitPrice,
                                             style=MarketOrder(), tif='DAY', accountCode='default', ocaGroup=None, orderRef=''):
        """
        # https://developer.tdameritrade.com/content/place-order-samples Not implemented for TD yet
        orderStatus of parentOrder is Submitted
        orderStatus of stoplossOrder and takeprofitOrder is PreSubmitted.
        !!! All three orders will cost margin, which means less margin for other trades.
        """
        self._brokerService.add_exchange_primaryExchange_to_security(security)
        if ocaGroup is None:
            ocaGroup = str(dt.datetime.now())
        adj_accountCode = self.adjust_accountCode(accountCode)
        int_parentOrderId = self._brokerService.use_next_id()
        parentOrder = create_order(int_parentOrderId, adj_accountCode, security, amount, style, self.get_datetime(),
                                   ocaGroup=ocaGroup, orderRef=orderRef)
        int_tpOrderId = self._brokerService.use_next_id()
        tpOrder = create_order(int_tpOrderId, adj_accountCode, security, -amount, LimitOrder(takeProfitPrice, tif=tif),
                               self.get_datetime(),
                               ocaGroup=ocaGroup, orderRef=orderRef)
        int_slOrderId = self._brokerService.use_next_id()
        slOrder = create_order(int_slOrderId, adj_accountCode, security, -amount, StopOrder(stopLossPrice, tif=tif),
                               self.get_datetime(),
                               ocaGroup=ocaGroup, orderRef=orderRef)
        # IB recommends this way to place takeProfitOrder and stopLossOrder
        # with main order.
        parentOrder.requestedOrder['transmit'] = False
        tpOrder.requestedOrder['parentId'] = int_parentOrderId
        slOrder.requestedOrder['parentId'] = int_parentOrderId
        tpOrder.requestedOrder['transmit'] = False
        slOrder.requestedOrder['transmit'] = True  # only transmit slOrder to avoid inadvertent actions

        # As IB recommended, parentOrder and takeProfitOrder are not transmitted, so that IBridgePy should not follow up
        str_parentOrderId = self._brokerService.place_order(parentOrder, followUp=False)
        str_tpOrderId = self._brokerService.place_order(tpOrder, followUp=False)
        str_slOrderId = self._brokerService.place_order(slOrder)
        return str_parentOrderId, str_slOrderId, str_tpOrderId

    def place_combination_orders(self, legList):
        ans = []
        for order in legList:
            ibpyOrderId = self._brokerService.place_order(order, followUp=False)
            ans.append(ibpyOrderId)
        return ans

    def modify_order(self, ibpyOrderId, newQuantity=None, newLimitPrice=None, newStopPrice=None, newTif=None,
                     newOrderRef=None, newOcaGroup=None, newOcaType=None):
        self._log.debug(__name__ + '::modify_order: ibpyOrderId = %s' % (ibpyOrderId,))
        currentOrder = self._brokerService.get_order(ibpyOrderId)
        if currentOrder.status in [OrderStatus.PRESUBMITTED, OrderStatus.SUBMITTED]:
            if newQuantity is not None:
                currentOrder.order['totalQuantity'] = newQuantity
            if newLimitPrice is not None:
                currentOrder.order['lmtPrice'] = newLimitPrice
            if newStopPrice is not None:
                currentOrder.order['auxPrice'] = newStopPrice
            if newTif is not None:
                currentOrder.order['tif'] = newTif
            if newOrderRef is not None:
                currentOrder.order['orderRef'] = newOrderRef
            if newOcaGroup is not None:
                currentOrder.order['ocaGroup'] = newOcaGroup
            if newOcaType is not None:
                currentOrder.order['ocaType'] = newOcaType
            self._brokerService.submit_requests(ModifyOrder(ibpyOrderId, currentOrder.contract, currentOrder.order,
                                                            FollowUpRequest.DO_NOT_FOLLOW_UP))
        else:
            self._log.error(__name__ + '::modify_order: Cannot modify ibpyOrderId=%s orderStatus=%s' % (ibpyOrderId, currentOrder.status))
            exit()

    def get_order_status(self, ibpyOrderId):
        """
        ibpyOrderId is unique for any orders in any session
        """
        return self._brokerService.get_order(ibpyOrderId).status

    def order_status_monitor(self, ibpyOrderId, target_status, waitingTimeInSeconds=30):
        """
        IBridgePy automatically follow up on the status of requests sent to brokers and terminate if the request is not
        confirmed with in 30 seconds. When placing order, IBridgePy only checks if the order is delivered to brokers but
        does not specifically check the order status. To specifically follow up on specific order status,
        order_status_monitor is used.
        :param ibpyOrderId: str
        :param target_status: either str or list[str]
        :param waitingTimeInSeconds: int
        :return: None
        """
        self._log.notset(__name__ + '::order_status_monitor: ibpyOrderId=%s target_status=%s' % (ibpyOrderId, target_status))
        if not isinstance(ibpyOrderId, str):
            self._log.error(__name__ + '::order_status_monitor: EXIT, ibpyOrderId=%s must be a string' % (ibpyOrderId,))
            exit()
        if ibpyOrderId == 'NoOrderPlaced':
            return
        self._brokerService.order_status_monitor(ibpyOrderId, target_status, waitingTimeInSeconds)

    def get_all_open_orders(self, accountCode='default'):
        adj_accountCode = self.adjust_accountCode(accountCode)
        return self._brokerService.get_all_open_orders(adj_accountCode)

    def get_order(self, ibpyOrderId):
        """
        tested at integ_test_cancel_all_order.py
        :param ibpyOrderId:
        :return: broker_factory::records_def::IbridgePyOrder
        """
        self._log.debug(__name__ + '::get_order: ibpyOrderId=%s' % (ibpyOrderId,))
        return self._brokerService.get_order(ibpyOrderId)

    def get_open_orders(self, security=None, accountCode='default'):
        """
        OrderStatus = APIPENDING, PENDINGSUBMIT, PENDINGCANCEL, PRESUBMITTED, SUBMITTED
        :param security: IBridgePy::quantopian::Security
        :param accountCode: string
        :return: a list of models::Order::IbridgePyOrder when security is not None. Otherwise, a dict: key=security, value=models::Order::IbridgePyOrder
        """
        self._log.debug(__name__ + '::get_open_orders')
        adj_accountCode = self.adjust_accountCode(accountCode)
        orderList = self._brokerService.get_all_open_orders(adj_accountCode)
        if security is None:
            ans = {}
            for ibridgePyOrder in orderList:
                securityAsKey = from_contract_to_security(ibridgePyOrder.contract)
                securityInList = _get_same_security_from_list(securityAsKey, ans)
                if securityInList is None:
                    ans[securityAsKey] = [ibridgePyOrder]
                else:
                    ans[securityInList].append(ibridgePyOrder)
        else:
            ans = []
            for ibridgePyOrder in orderList:
                # print(ibridgePyOrder)
                if check_same_security(from_contract_to_security(ibridgePyOrder.contract), security):
                    ans.append(ibridgePyOrder)
        return ans

    def get_all_orders(self, accountCode='default'):
        """
        For Web-api-based brokers, it return all orders that are returned from the broker.
        But brokers may not return all orders. For example, IB returns only OPEN orders.
        :param accountCode:
        :return: dictionary keyed=ibpyOrderId value= {@models::Order::IbridgePyOrder}
        """
        self._log.debug(__name__ + '::get_all_orders')
        adj_accountCode = self.adjust_accountCode(accountCode)
        orderIdList = self._brokerService.get_all_orders(adj_accountCode)
        ans = {}
        for ibpyOrderId in orderIdList:
            ans[ibpyOrderId] = self.get_order(ibpyOrderId)
        return ans

    def get_all_positions(self, accountCode='default'):
        """

        :param accountCode: string
        :return: dictionary, keyed by Security object, value = PositionRecord
        """
        self._log.debug(__name__ + '::get_all_positions')
        adj_accountCode = self.adjust_accountCode(accountCode)
        return self._brokerService.get_all_positions(adj_accountCode)

    def get_position(self, security, accountCode='default'):
        """

        :param security:
        :param accountCode:
        :return: models::Position::PositionRecord If there is no position for the security, return a PositionRecord .amount=0 .cost_basis=0.0
        """
        self._log.debug(__name__ + '::get_position: security=%s' % (security,))
        adj_accountCode = self.adjust_accountCode(accountCode)

        # There is no need to add exchange and primaryExchange because the key of positions does not have exchange and primaryExchange
        # self.brokerService.add_exchange_primaryExchange_to_security(security)
        return self._brokerService.get_position(adj_accountCode, security)

    def _check_schedules(self):
        timeNow = self.get_datetime().astimezone(self._sysTimeZone)
        self._log.notset(__name__ + '::_check_schedules: timeNow=%s' % (timeNow,))
        # ct is an instance of class TimeBasedRules in quantopian.py
        for ct in self.scheduledFunctionList:
            if special_match(ct.onHour, timeNow.hour, 'hourMinute') and \
                    special_match(ct.onMinute, timeNow.minute, 'hourMinute') and \
                    special_match(ct.onSecond, timeNow.second, 'hourMinute') and \
                    special_match(ct.onNthMonthDay, self._marketCalendar.nth_trading_day_of_month(timeNow),
                                  'monthWeek') and \
                    special_match(ct.onNthWeekDay, self._marketCalendar.nth_trading_day_of_week(timeNow), 'monthWeek'):
                ct.func(self.context, self.qData)

    def schedule_function(self,
                          func,
                          date_rule=None,
                          time_rule=None,
                          calendar=calendars.US_EQUITIES):
        """
        ONLY time_rule.spot_time depends on
        :param func: the function to be run at sometime
        :param date_rule: IBridgePy::quantopian::date_rule
        :param time_rule: BridgePy::quantopian::time_rule
        :param calendar: typical market open close time
        :return: self.scheduledFunctionList
        """

        onHour = None
        onMinute = None
        onSecond = None
        self._log.debug(__name__ + '::schedule_function')
        if time_rule is None:
            onHour = 'any'  # every number can match, run every hour
            onMinute = 'any'  # every number can match, run every minute
            onSecond = 'any'
        else:
            # if there is a time_rule, calculate onHour and onMinute based on market times
            marketOpenHour, marketOpenMinute, marketCloseHour, marketCloseMinute = calendar
            # print (marketOpenHour,marketOpenMinute,marketCloseHour,marketCloseMinute)
            marketOpen = marketOpenHour * 60 + marketOpenMinute
            marketClose = marketCloseHour * 60 + marketCloseMinute
            if time_rule.version == 'market_open' or time_rule.version == 'market_close':
                if time_rule.version == 'market_open':
                    tmp = marketOpen + time_rule.hour * 60 + time_rule.minute
                else:
                    tmp = marketClose - time_rule.hour * 60 - time_rule.minute
                while tmp < 0:
                    tmp += 24 * 60
                startTime = tmp % (24 * 60)
                onHour = int(startTime / 60)
                onMinute = int(startTime % 60)
                onSecond = 0
            elif time_rule.version == 'spot_time':
                onHour = time_rule.hour
                onMinute = time_rule.minute
                onSecond = time_rule.second
            else:
                self._log.error(
                    __name__ + '::schedule_function: EXIT, cannot handle time_rule.version=%s' % (time_rule.version,))
                exit()

        if date_rule is None:
            # the default rule is None, means run every_day
            tmp = TimeBasedRules(onHour=onHour, onMinute=onMinute, onSecond=onSecond, func=func)
            self.scheduledFunctionList.append(tmp)
            return
        else:
            if date_rule.version == 'every_day':
                tmp = TimeBasedRules(onHour=onHour, onMinute=onMinute, onSecond=onSecond, func=func)
                self.scheduledFunctionList.append(tmp)
                return
            else:
                if date_rule.version == 'week_start':
                    onNthWeekDay = date_rule.weekDay
                    tmp = TimeBasedRules(onNthWeekDay=onNthWeekDay,
                                         onHour=onHour,
                                         onMinute=onMinute,
                                         onSecond=onSecond,
                                         func=func)
                    self.scheduledFunctionList.append(tmp)
                    return
                elif date_rule.version == 'week_end':
                    onNthWeekDay = -date_rule.weekDay - 1
                    tmp = TimeBasedRules(onNthWeekDay=onNthWeekDay,
                                         onHour=onHour,
                                         onMinute=onMinute,
                                         onSecond=onSecond,
                                         func=func)
                    self.scheduledFunctionList.append(tmp)
                    return
                if date_rule.version == 'month_start':
                    onNthMonthDay = date_rule.monthDay
                    tmp = TimeBasedRules(onNthMonthDay=onNthMonthDay,
                                         onHour=onHour,
                                         onMinute=onMinute,
                                         onSecond=onSecond,
                                         func=func)
                    self.scheduledFunctionList.append(tmp)
                    return
                elif date_rule.version == 'month_end':
                    onNthMonthDay = -date_rule.monthDay - 1
                    tmp = TimeBasedRules(onNthMonthDay=onNthMonthDay,
                                         onHour=onHour,
                                         onMinute=onMinute,
                                         onSecond=onSecond,
                                         func=func)
                    self.scheduledFunctionList.append(tmp)
                    return

    @staticmethod
    def symbol(str_security):
        security = from_symbol_to_security(str_security)

        # Try to minimize the usage of security_info.csv
        # Only add exchange and primaryExchange when it needs to send requests to IB server
        # self.brokerService.add_exchange_primaryExchange_to_security(security)
        return security

    ''' Another way to make symbol
    class symbol(Security):
        def __init__(self, str_security):
            if ',' not in str_security:
                str_security = 'STK,%s,USD' % (str_security,)

            secType = str_security.split(',')[0].strip()
            ticker = str_security.split(',')[1].strip()
            currency = str_security.split(',')[2].strip()
            if secType in ['CASH', 'STK']:
                Security.__init__(self, secType=secType, symbol=ticker, currency=currency)
            else:
                print('Definition of %s is not clear!' % (s1,))
                print('Please use superSymbol to define a str_security')
                print(r'http://www.ibridgepy.com/ibridgepy-documentation/#superSymbol')
                exit()
    '''

    def symbols(self, *args):
        ans = []
        for item in args:
            ans.append(self.symbol(item))
        return ans

    def calculate_cash_for_trade_deprecated(self, accountCode='default'):
        """
        it is deprecated because different users have different account type(cash vs margin). If they trade options, futures
        and others, the way to calculated the amount to trade is different. IBridgePy should not do it for users and users
        should know which value they should use, especially for IB users.
        """
        self._log.debug(__name__ + '::calculate_cash_for_trade_deprecated:')
        adj_accountCode = self.adjust_accountCode(accountCode)
        orderDict = self.get_all_orders(adj_accountCode)
        cashOccupied = 0.0
        for ibpyOrderId in orderDict:
            order = orderDict[ibpyOrderId]
            if order.status in [OrderStatus.SUBMITTED, OrderStatus.PRESUBMITTED]:
                orderType = order.get_value_by_tag('orderType')
                if orderType == OrderType.LMT:
                    cashOccupied += order.limit * order.amount
                elif orderType == OrderType.STP:
                    cashOccupied += order.stop * order.amount
                elif orderType == OrderType.STP_LMT:
                    cashOccupied += order.limit * order.amount
                    cashOccupied += order.stop * order.amount
        return self._brokerService.get_account_info(adj_accountCode, 'AvailableFunds') - cashOccupied

    # noinspection PyTypeChecker
    def close_all_positions_LMT(self, ls_excludeSecurities, advantage, orderStatusMonitor=True, accountCode='default'):
        self._log.debug(__name__ + '::close_all_positions_LMT:')
        # if advantage < 0.0:
        #     self._log.error(__name__ + '::close_all_positions_LMT: EXIT, advantage=%s must > 0.0' % (advantage,))
        #     exit()
        adj_accountCode = self.adjust_accountCode(accountCode)
        positions = self.get_all_positions(adj_accountCode)  # return a dictionary
        orderIdList = []

        # !!! cannot iterate positions directly because positions can change during the iteration if any orders are
        # executed.
        # The solution is to use another list to record all security to be closed.
        adj_securities = list(positions.keys())

        # place close orders
        for security in adj_securities:
            if not _is_in_security_list(security, ls_excludeSecurities):
                holding_quantity = self.get_position(security, adj_accountCode).amount
                if Decimal(holding_quantity) > 0:
                    bid_price = self.show_real_time_price(security, 'bid_price')
                    limitPrice = roundToMinTick(bid_price * (1.0 + advantage))
                    self._log.info(__name__ + '::close_all_positions_LMT: bid_price=%s, sellAtLimitPrice=%s' % (bid_price, limitPrice))
                    ibpyOrderId = self.order(security, str(-1 * Decimal(holding_quantity)),
                                             style=LimitOrder(limitPrice, tif=OrderTif.GTC),
                                             accountCode=adj_accountCode)
                else:
                    ask_price = self.show_real_time_price(security, 'ask_price')
                    limitPrice = roundToMinTick(ask_price * (1.0 - advantage))
                    self._log.info(__name__ + '::close_all_positions_LMT: ask_price=%s, buyAtLimitPrice=%s' % (ask_price, limitPrice))
                    ibpyOrderId = self.order(security, str(-1 * Decimal(holding_quantity)),
                                             style=LimitOrder(limitPrice, tif=OrderTif.GTC),
                                             accountCode=adj_accountCode)
                orderIdList.append(ibpyOrderId)

        # Monitor status
        if orderStatusMonitor:
            for ibpyOrderId in orderIdList:
                self.order_status_monitor(ibpyOrderId, OrderStatus.FILLED)

    # noinspection PyTypeChecker
    def rebalance_portfolio(self, traderDecisions, buyAdvantage=0.0, sellAdvantage=0.0, accountCode='default'):
        """
        Used for IB only because processMessage() will be very slow for WebAPI based brokers.
        :param sellAdvantage:
        :param buyAdvantage: take advantages when place buy orders at ask_price * (1 - bugAdvantage), positive == take advantage. negative == disadvantage.
        :param accountCode:
        :param traderDecisions: dict key=security value=target number of share
        :return:
        """
        adj_accountCode = self.adjust_accountCode(accountCode)
        startTime = dt.datetime.now()
        count = len(traderDecisions)

        if count == 0:  # decision is to hold NOTHING
            self.close_all_positions_LMT(ls_excludeSecurities=[], advantage=sellAdvantage, orderStatusMonitor=False, accountCode=adj_accountCode)
            return

        # Decision is to buy something, continue ...

        # If contracts are not in the wish-list, it means do not hold them. So, sell them at first place to free up cash
        self._log.info('Start to sell securities not in the traderDecisions')
        self.close_all_positions_LMT(ls_excludeSecurities=traderDecisions.keys(), advantage=sellAdvantage, orderStatusMonitor=False, accountCode=adj_accountCode)
        self._log.info('Finished to sell securities not in the traderDecisions')

        # Calculate number of share to buy or sell based on holding amount
        # save them to sellSecurityDict and buySecurityDict so that sell first and then buy.
        sellSecurityDict = {}  # key=Security; value=real number of shares needs to sell, negative number
        buySecurityDict = {}  # key=Security; value=real number of shares needs to buy, positive number
        for security in traderDecisions:
            holding_quantity = self.get_position(security, adj_accountCode).amount
            target_quantity = traderDecisions[security]
            if Decimal(target_quantity) < Decimal(holding_quantity):
                sellSecurityDict[security] = Decimal(target_quantity) - Decimal(holding_quantity)  # must be negative number
            elif Decimal(target_quantity) > Decimal(holding_quantity):
                buySecurityDict[security] = Decimal(target_quantity) - Decimal(holding_quantity)  # must be positive number
            else:
                self._log.debug('No action for security=%s' % (security,))

        self._log.info('sellSecurityDict=%s' % (print_decisions(sellSecurityDict),))
        self._log.info('buySecurityDict=%s' % (print_decisions(buySecurityDict),))
        # Sell contracts to free up cash to buy others later
        sellOrderIds = []
        for security in sellSecurityDict:
            bid_price = self.show_real_time_price(security, 'bid_price')
            ibpyOrderId = self.order(security,
                                     sellSecurityDict[security],  # negative number here
                                     style=LimitOrder(roundToMinTick(bid_price * (1.0 + sellAdvantage)), tif=OrderTif.GTC),
                                     # 1.0001 = take some advantage here. Selling above the current bid price
                                     followUp=FollowUpRequest.DO_NOT_FOLLOW_UP,
                                     # Dont follow up so that orders are placed as early as possible
                                     accountCode=adj_accountCode)
            sellOrderIds.append(ibpyOrderId)
        for oid in sellOrderIds:
            self.order_status_monitor(oid, ['Filled', 'Submitted'])

        # Wait for cash that are freed up by selling others to buy contracts
        # However, the wait should last forever. The setting here is to wait 1 minute
        buyOrderIds = []
        previous_available_fund = 0.0
        while len(buySecurityDict) > 0 and (dt.datetime.now() - startTime).total_seconds() < 60 * 5:
            # Cannot delete in for-loop. Have to record them and delete them after for-loop
            toBeDeleted = []

            # Buy as much as possible according to available funds for trade
            available_fund = self.show_account_info('AvailableFunds', accountCode=adj_accountCode)

            if abs(available_fund - previous_available_fund) <= 0.99:
                self._log.info(__name__ + '::rebalance_portfolio: available_fund has not been updated. Do not continue to place orders. Sleep 3 seconds')
                time.sleep(3)
                self.processMessages(self.get_datetime())
                continue

            # Record available_fund. The change of available_fund means that some orders have been updated and 20200923 assume that
            # the available_fund from self.show_account_info is updated correctly
            previous_available_fund = available_fund

            self._log.info(__name__ + '::rebalance_portfolio: available_fund=%s' % (available_fund,))
            self.display_all()
            for security in buySecurityDict:
                ask_price = self.show_real_time_price(security, 'ask_price')
                # print(security.full_print(), 'ask_price=', ask_price)
                target_quantity = buySecurityDict[security]

                # check available funds and buy as much as possible
                purchase_amount = min(target_quantity, int(available_fund / ask_price))
                limitPrice = roundToMinTick(ask_price * (1.0 - buyAdvantage))
                # print(security.full_print(), limitPrice)
                if purchase_amount > 0:
                    try:
                        ibpyOrderId = self.order(security,
                                                 purchase_amount,  # must be positive here
                                                 style=LimitOrder(limitPrice, tif=OrderTif.GTC),
                                                 accountCode=adj_accountCode,
                                                 followUp=FollowUpRequest.DO_NOT_FOLLOW_UP)
                        buyOrderIds.append(ibpyOrderId)
                        buySecurityDict[security] -= purchase_amount
                        # in the for loop, only calculate available_fund to avoid getting data from server
                        available_fund = Decimal(available_fund) - Decimal(limitPrice) * purchase_amount
                        self._log.info(__name__ + '::rebalance_portfolio: virtual available_fund=%s' % (available_fund,))
                    except NotEnoughFund:
                        self._log.info(__name__ + '::rebalance_portfolio: Not enough fund but it is ok to continue')
                elif purchase_amount < 0:
                    self._log.error(__name__ + '::rebalance_portfolio: EXIT, purchase_amount=%s target_quantity=%s available_fund=%s ask_price=%s' % (purchase_amount, target_quantity, available_fund, ask_price))
                    exit()
                # have bought all target amount, no more action. ready to remove it from wish-list
                if buySecurityDict[security] <= 0:
                    toBeDeleted.append(security)
            # Remove those securities that have been bought from wish-list
            for security in toBeDeleted:
                del buySecurityDict[security]

            time.sleep(3)
            self._log.info(__name__ + '::rebalance_portfolio: waited for 3 seconds')
            self.processMessages(self.get_datetime())
        self._log.info(__name__ + '::rebalance_portfolio: completed')
        return sellOrderIds + buyOrderIds

    def isTradingDay(self):
        return self._marketCalendar.isTradingDay(self.get_datetime())

    def isEarlyClose(self):
        return self._marketCalendar.isEarlyClose(self.get_datetime())

    def record(self, *args, **kwargs):
        self._userLog.record(*args, **kwargs)

    def send_email(self, emailTitle, emailBody, toEmail=None):
        self._emailClient.send_email(emailTitle, emailBody, toEmail)

    def get_5_second_real_time_bar(self, security, tickType):
        self._log.notset(f'{__name__}::get_5_second_real_time_bar: security={security} tickType={tickType}')
        self._dataProviderService.add_exchange_primaryExchange_to_security(security)
        return self._brokerService.get_5_second_real_time_bar(security, tickType)
