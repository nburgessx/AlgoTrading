# -*- coding: utf-8 -*-
"""
@author: IBridgePy@gmail.com
"""
from BasicPyLib.BasicTools import CONSTANTS

"""
This module defines the constants used by IB.
For other brokers, checkout broker_client_factory::TdAmeritrade::BrokerClient_TdAmeritrade.py. There are a few converters
"""


class SecType(CONSTANTS):
    CASH = 'CASH'
    STK = 'STK'
    FUT = 'FUT'
    OPT = 'OPT'
    IND = 'IND'
    CFD = 'CFD'
    BOND = 'BOND'


class LiveBacktest(CONSTANTS):
    LIVE = 1
    BACKTEST = 2


class BrokerName(CONSTANTS):
    LOCAL = 'LOCAL'
    IB = 'IB'
    ROBINHOOD = 'ROBINHOOD'
    TD = 'TD'
    IBRIDGEPY = 'IBRIDGEPY'
    IBinsync = 'IBinsync'


class BrokerServiceName(CONSTANTS):
    LOCAL_BROKER = 'LOCAL'
    IB = 'IB'
    ROBINHOOD = 'ROBINHOOD'
    TD = 'TD'
    IBRIDGEPY = 'IBRIDGEPY'
    IBinsync = 'IBinsync'


class BrokerClientName(CONSTANTS):
    LOCAL = 'LOCAL'
    IB = 'IB'
    ROBINHOOD = 'ROBINHOOD'
    TD = 'TD'
    IBinsync = 'IBinsync'


class DataProviderName(CONSTANTS):
    LOCAL_FILE = 'LOCAL_FILE'
    RANDOM = 'RANDOM'
    IB = 'IB'
    TD = 'TD'
    ROBINHOOD = 'ROBINHOOD'
    IBRIDGEPY = 'IBRIDGEPY'
    IBinsync = 'IBinsync'
    YAHOO_FINANCE = 'YahooFinance'


class DataSourceName(CONSTANTS):
    IB = 'IB'
    YAHOO = 'YAHOO'
    GOOGLE = 'GOOGLE'
    LOCAL_FILE = 'LOCAL_FILE'
    SIMULATED_BY_DAILY_BARS = 'simulatedByDailyBars'


class SymbolStatus(CONSTANTS):
    DEFAULT = 0
    SUPER_SYMBOL = 1
    ADJUSTED = 2
    STRING_CONVERTED = 3


class TraderRunMode(CONSTANTS):
    REGULAR = 'REGULAR'
    RUN_LIKE_QUANTOPIAN = 'RUN_LIKE_QUANTOPIAN'
    SUDO_RUN_LIKE_QUANTOPIAN = 'SUDO_RUN_LIKE_QUANTOPIAN'
    HFT = 'HFT'


class OrderStatus(CONSTANTS):
    """
    The values should match IB's order status value in string
    """
    PRESUBMITTED = 'PreSubmitted'
    SUBMITTED = 'Submitted'
    CANCELLED = 'Cancelled'
    APIPENDING = 'ApiPending'
    PENDINGSUBMIT = 'PendingSubmit'
    PENDINGCANCEL = 'PendingCancel'
    FILLED = 'Filled'
    INACTIVE = 'Inactive'


class OrderAction(CONSTANTS):
    BUY = 'BUY'
    SELL = 'SELL'


class OrderTif(CONSTANTS):
    DAY = 'DAY'  # good for today
    GTC = 'GTC'  # good to cancel


class OrderType(CONSTANTS):
    MKT = 'MKT'
    LMT = 'LMT'
    STP = 'STP'
    TRAIL_LIMIT = 'TRAIL LIMIT'
    TRAIL = 'TRAIL'
    STP_LMT = 'STP LMT'
    NET_CREDIT = 'NET CREDIT'  # TD Amertride term


class ExchangeName(CONSTANTS):
    ISLAND = 'ISLAND'


class MarketName(CONSTANTS):
    NYSE = 'NYSE'
    NONSTOP = 'NONSTOP'


class Default(CONSTANTS):
    DEFAULT = 'default'


class FollowUpRequest(CONSTANTS):
    DO_NOT_FOLLOW_UP = False
    FOLLOW_UP = True


class RequestDataParam(CONSTANTS):
    WAIT_30_SECONDS = 30
    WAIT_1_SECOND = 1
    DO_NOT_REPEAT = 0


class LogLevel(CONSTANTS):
    ERROR = 'ERROR'
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    NOTSET = 'NOTSET'


class TimeGeneratorType(CONSTANTS):
    LIVE = 'LIVE'
    AUTO = 'AUTO'
    CUSTOM = 'CUSTOM'


class TimeConcept(CONSTANTS):
    NEW_DAY = 'new_day'
    NEW_HOUR = 'new_hour'


class ReqType(CONSTANTS):
    REQ_POSITIONS = 'reqPositions'
    REQ_CONNECT = 'reqConnect'
    REQ_CURRENT_TIME = 'reqCurrentTime'
    REQ_ALL_OPEN_ORDERS = 'reqAllOpenOrders'
    REQ_ONE_ORDER = 'reqOneOrder'
    REQ_ACC_UPDATES = 'reqAccountUpdates'
    REQ_ACC_SUMMARY = 'reqAccountSummary'
    REQ_IDS = 'reqIds'
    REQ_HEART_BEATS = 'reqHeartBeats'
    REQ_HIST_DATA = 'reqHistoricalData'
    REQ_MKT_DATA = 'reqMktData'
    REQ_CANCEL_MKT_DATA = 'cancelMktData'
    REQ_REAL_TIME_BARS = 'reqRealTimeBars'
    REQ_PLACE_ORDER = 'placeOrder'
    REQ_MODIFY_ORDER = 'modifyOrder'
    REQ_CONTRACT_DETAILS = 'reqContractDetails'
    REQ_CALCULATE_IMPLI_VOL = 'calculateImpliedVolatility'
    REQ_SCANNER_SUB = 'reqScannerSubscription'
    REQ_CANCEL_SCANNER_SUB = 'cancelScannerSubscription'
    REQ_CANCEL_ORDER = 'cancelOrder'
    REQ_SCANNER_PARA = 'reqScannerParameters'


if __name__ == '__main__':
    pass
