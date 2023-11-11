# coding=utf-8
from sys import exit

import pandas as pd
import json

# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.constants import SymbolStatus


def from_contract_to_security(contract):
    if isinstance(contract, str):
        if contract:
            contract = json.loads(contract)
            if isinstance(contract, str):
                contract = json.loads(contract)
        else:
            contract = {}
    elif isinstance(contract, dict):
        pass
    else:
        contract = vars(contract)
    ans = Security(secType=contract['secType'], symbol=contract['symbol'], currency=contract['currency'])
    for para in ['secType', 'symbol', 'primaryExchange', 'exchange', 'currency', 'lastTradeDateOrContractMonth', 'strike', 'right', 'multiplier', 'localSymbol']:
        tmp = contract.get(para, '')
        if tmp != '':
            setattr(ans, para, tmp)
    return ans


def from_security_to_contract(security):
    contract = {'symbol': security.symbol,
                'secType': security.secType,
                'exchange': security.exchange,
                'currency': security.currency,
                'primaryExchange': security.primaryExchange,
                'includeExpired': security.includeExpired,
                'lastTradeDateOrContractMonth': security.expiry,
                'strike': float(security.strike),
                'right': security.right,
                'multiplier': security.multiplier,
                'localSymbol': security.localSymbol,
                'conId': security.conId}
    return json.dumps(contract)


# Quantopian compatible data structures
class Security(object):
    def __init__(self,
                 secType=None,
                 symbol=None,
                 currency='USD',
                 exchange='',  # default value, when IB returns contract
                 primaryExchange='',  # default value, when IB returns contract
                 expiry='',
                 strike=0.0,  # default value=0.0, when IB returns contract
                 right='',
                 multiplier='',  # default value, when IB returns contract
                 includeExpired=False,
                 sid=-1,
                 conId=0,  # for special secType, conId must be used.
                 localSymbol='',
                 security_name=None,
                 security_start_date=None,
                 security_end_date=None,
                 symbolStatus=SymbolStatus.DEFAULT):
        self.secType = secType
        self.symbol = symbol
        self.currency = currency
        self.exchange = exchange
        self.primaryExchange = primaryExchange
        self.expiry = expiry
        self.strike = strike
        self.right = right
        self.multiplier = multiplier
        self.includeExpired = includeExpired
        self.sid = sid
        self.conId = conId
        self.localSymbol = localSymbol
        self.security_name = security_name
        self.security_start_date = security_start_date
        self.security_end_date = security_end_date
        self.symbolStatus = symbolStatus

    def __str__(self):
        if self.secType in ['FUT', 'BOND']:
            return '%s,%s,%s,%s' % (self.secType, self.symbol, self.currency, self.expiry)
        elif self.secType == 'CASH':
            return 'CASH,%s,%s' % (self.symbol, self.currency)
        elif self.secType == 'OPT':
            return 'OPT,%s,%s,%s,%s,%s,%s' % (self.symbol, self.currency, self.expiry, self.strike, self.right, self.multiplier)
        else:
            return '%s,%s,%s' % (self.secType, self.symbol, self.currency)

    def __eq__(self, security):
        return self.full_print() == security.full_print()

    def __hash__(self):
        return id(self)

    def full_print(self):  # VERY IMPORTANT because context.portfolio.positions using security.full_print as the key.
        if self.secType in ['FUT', 'BOND']:
            return '%s,%s,%s,%s,%s,%s' % (self.secType, self.primaryExchange, self.exchange, self.symbol, self.currency, self.expiry)
        elif self.secType in ['CASH', 'STK', 'CMDTY', 'IND', 'CFD']:
            return '%s,%s,%s,%s,%s' % (self.secType, self.primaryExchange, self.exchange, self.symbol, self.currency)
        # strike needs to be formatted in same way. Otherwise, context.portfolio.positions[superSymbol[xxx]) will show 0
        # because strike is not the same.
        else:
            return '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (self.secType, self.primaryExchange, self.exchange, self.symbol, self.currency,
                                                      self.expiry, "{:10.2f}".format(self.strike), self.right, self.multiplier, self.localSymbol)


class QDataClass(object):
    """
    This is a wrapper to match quantopian's data.current and data.history
    """

    def __init__(self, parentTrader):
        self.data = {}
        self.dataHash = {}
        self.parentTrader = parentTrader

    def current(self, security, field):
        if type(security) == list and type(field) != list:
            ans = {}
            for ct in security:
                ans[ct] = self.current_one(ct, field)
            return pd.Series(ans)
        elif type(security) == list and type(field) == list:
            ans = {}
            for ct1 in field:
                ans[ct1] = {}
                for ct2 in security:
                    ans[ct1][ct2] = self.current_one(ct2, ct1)
            return pd.DataFrame(ans)
        elif type(security) != list and type(field) == list:
            ans = {}
            for ct in field:
                ans[ct] = self.current_one(security, ct)
            return pd.Series(ans)
        else:
            return self.current_one(security, field)

    def current_one(self, security, version):
        self.parentTrader.getLog().notset(__name__ + '::current_one: security=%s version=%s' % (security, version))
        if version in ['ask_price', 'bid_price', 'price', 'last_price', 'open', 'high', 'low', 'close']:
            return self.parentTrader.show_real_time_price(security, version)
        elif version in ['ask_size', 'bid_size', 'volume']:
            return self.parentTrader.show_real_time_size(security, version)

    def history(self, security, fields, bar_count, frequency, followUp=True):
        goBack = None
        if frequency == '1d':
            frequency = '1 day'
            if bar_count > 365:
                goBack = str(int(bar_count / 365.0) + 1) + ' Y'
            else:
                goBack = str(bar_count) + ' D'
        elif frequency == '1m':
            frequency = '1 min'
            goBack = str(bar_count * 60) + ' S'
        elif frequency == '30m':
            frequency = '30 mins'
            goBack = str(int(bar_count / 13.0) + 2) + ' D'
        elif frequency == '1 hour' or frequency == '1h':
            goBack = str(int(bar_count / 6.5) + 2) + ' D'
        else:
            print(__name__ + '::history: EXIT, cannot handle frequency=%s' % (str(frequency, )))
            exit()
        if type(security) != list:
            return self.history_one(security, fields, goBack, frequency, followUp).tail(bar_count)
        else:
            if type(fields) == str:
                ans = {}
                for sec in security:
                    ans[sec] = self.history_one(sec, fields, goBack, frequency, followUp).tail(bar_count)
                return pd.DataFrame(ans)
            else:
                tmp = {}
                for sec in security:
                    tmp[sec] = self.history_one(sec, fields, goBack, frequency, followUp).tail(bar_count)
                ans = {}
                for fld in fields:
                    ans[fld] = {}
                    for sec in security:
                        ans[fld][sec] = tmp[sec][fld]
                return pd.DataFrame(ans,
                                    columns=ans.keys())

    def history_one(self, security, fields, goBack, frequency, followUp=True):
        tmp = self.parentTrader.request_historical_data(security, frequency, goBack, followUp=followUp)
        if len(tmp) == 0:
            return pd.Series()

        # Add a new column called "price" and fill it by the column of "close"
        # This is how quantopian returns
        tmp = tmp.assign(price=tmp.close)
        tmp['price'].fillna(method='pad')
        return tmp[fields]

    @staticmethod
    def can_trade(security):
        """
        This function is provided by Quantopian.
        IBridgePy supports the same function.
        However, as of 20180128, IBridgePy will not check if the str_security is
        tradeable.
        In the future, IBridgePy will check it.
        Input: Security
        Output: Bool
        """
        if security:  # Remove pep8 warning
            return True
        return True


class TimeBasedRules(object):
    def __init__(self, onNthMonthDay='any',
                 onNthWeekDay='any',
                 onHour='any',
                 onMinute='any',
                 onSecond='any',
                 func=None):
        self.onNthMonthDay = onNthMonthDay
        self.onNthWeekDay = onNthWeekDay  # Monday=0, Friday=4
        self.onHour = onHour
        self.onMinute = onMinute
        self.onSecond = onSecond
        self.func = func

    def __str__(self):
        return str(self.onNthMonthDay) + ' ' + str(self.onNthWeekDay) \
               + ' ' + str(self.onHour) + ' ' + str(self.onMinute) + ' ' + str(self.func)


# noinspection PyPep8Naming
class calendars(object):
    US_EQUITIES = (9, 30, 16, 0)
    US_FUTURES = (6, 30, 17, 0)


# noinspection PyPep8Naming
class time_rules(object):
    # noinspection PyPep8Naming
    class market_open(object):
        def __init__(self, hours=0, minutes=1):
            self.hour = hours
            self.minute = minutes
            self.second = 0
            self.version = 'market_open'

    # noinspection PyPep8Naming
    class market_close(object):
        def __init__(self, hours=0, minutes=1):
            self.hour = hours
            self.minute = minutes
            self.second = 0
            self.version = 'market_close'

    # noinspection PyPep8Naming
    class spot_time(object):
        def __init__(self, hour=0, minute=0, second=0):
            self.hour = hour
            self.minute = minute
            self.second = second
            self.version = 'spot_time'


# noinspection PyPep8Naming
class date_rules(object):
    # noinspection PyPep8Naming
    class every_day(object):
        def __init__(self):
            self.version = 'every_day'

    # noinspection PyPep8Naming
    class week_start(object):
        def __init__(self, days_offset=0):
            self.weekDay = days_offset
            self.version = 'week_start'

    # noinspection PyPep8Naming
    class week_end(object):
        def __init__(self, days_offset=0):
            self.weekDay = days_offset
            self.version = 'week_end'

    # noinspection PyPep8Naming
    class month_start(object):
        def __init__(self, days_offset=0):
            self.monthDay = days_offset
            self.version = 'month_start'

    # noinspection PyPep8Naming
    class month_end(object):
        def __init__(self, days_offset=0):
            self.monthDay = days_offset
            self.version = 'month_end'
