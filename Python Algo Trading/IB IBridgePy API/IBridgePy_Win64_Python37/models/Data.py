# coding=utf-8
from sys import exit
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from BasicPyLib.Printable import PrintableII


class TickPriceRecord(PrintableII):
    def __init__(self, str_security, tickType, price, canAutoExecute, timestamp=None):
        self.str_security = str_security
        self.tickType = tickType
        self.price = price
        self.canAutoExecute = canAutoExecute
        self.timestamp = timestamp


class TickSizeRecord(PrintableII):
    def __init__(self, str_security, tickType, size):
        self.str_security = str_security
        self.tickType = tickType
        self.size = size


class TickStringRecord(PrintableII):
    def __init__(self, str_security, tickType, value):
        self.str_security = str_security
        self.tickType = tickType
        self.value = value


class TickOptionComputationRecord(object):
    def __init__(self, str_security, tickType, tickAttrib, impliedVol, delta,
                 optPrice, pvDividend, gamma, vega, theta,
                 undPrice):
        self.str_security = str_security
        self.tickType = tickType
        self.tickAttrib = tickAttrib
        self.impliedVol = impliedVol
        self.delta = delta
        self.optPrice = optPrice
        self.pvDividend = pvDividend
        self.gamma = gamma
        self.vega = vega
        self.theta = theta
        self.undPrice = undPrice


class KeyedTickInfoRecords(object):
    """
    tickPrice, tickSize, tickString and tickOptionComputation
    All of them are stored in same way, 1st key = str_security and 2nd key = tickType.
    So that one KeyedTickInfoRecords is needed as a template for 4 records
    """

    def __init__(self, fieldNameAsKey):
        self.keyedTickInfoRecords = {}  # 1st key = str_security and 2nd key = tickType.
        self.fieldNameAsKey = fieldNameAsKey

    def __str__(self):
        if len(self.keyedTickInfoRecords) == 0:
            return 'Empty keyedTickInfoRecords id=%s' % (id(self),)
        ans = ''
        for str_security in self.keyedTickInfoRecords:
            for key in self.keyedTickInfoRecords[str_security]:
                ans += '%s:%s:%s\n' % (str_security, key, self.keyedTickInfoRecords[str_security][key])
        return ans[:-1]

    def update(self, tickInfoRecord):
        if not hasattr(tickInfoRecord, 'str_security'):
            print(__name__ + '::update: EXIT, %s does not have attr of %s' % (tickInfoRecord, 'str_security'))
            exit()

        str_security = tickInfoRecord.str_security
        if not isinstance(str_security, str):  # Make sure str_security is a string
            print(__name__ + '::update: EXIT, type of str_security=%s is not correct' % (type(str_security),))
            exit()

        if str_security not in self.keyedTickInfoRecords:
            self.keyedTickInfoRecords[str_security] = {}
        if hasattr(tickInfoRecord, self.fieldNameAsKey):
            key = getattr(tickInfoRecord, self.fieldNameAsKey)
            self.keyedTickInfoRecords[str_security][key] = tickInfoRecord
        else:
            print(__name__ + '::update: EXIT, %s does not have attr of %s' % (tickInfoRecord, self.fieldNameAsKey))
            exit()

    def _hasSecurity(self, str_security):
        return str_security in self.keyedTickInfoRecords

    def _hasSecurityAndTickType(self, str_security, tickType):
        return self._hasSecurity(str_security) and (tickType in self.keyedTickInfoRecords[str_security])

    def get_value(self, security, tickType, fieldName):
        str_security = security.full_print()
        # print(__name__ + '::KeyedTickInfoRecords::get_value: str_security=%s tickType=%s fieldName=%s' % (str_security, tickType, fieldName))
        if self._hasSecurityAndTickType(str_security, tickType):
            if hasattr(self.keyedTickInfoRecords[str_security][tickType], fieldName):
                return getattr(self.keyedTickInfoRecords[str_security][tickType], fieldName)
            # else:
            #     print(__name__ + '::get_value: fieldName=%s not in record' % (fieldName, ))
        # else:
        #     print(__name__ + '::get_value: hasSecurityAndTickType failed str_security=%s tickType=%s' % (str_security, tickType))
        #     print(self.keyedTickInfoRecords)
        return None


class DataFromServer(object):
    """
    The interface for outside world to use
    """

    def __init__(self):
        self.tickPriceRecords = KeyedTickInfoRecords(fieldNameAsKey='tickType')
        self.tickSizeRecords = KeyedTickInfoRecords(fieldNameAsKey='tickType')
        self.tickStringRecords = KeyedTickInfoRecords(fieldNameAsKey='tickType')
        self.tickOptionComputationRecords = KeyedTickInfoRecords(fieldNameAsKey='tickType')
        self.latest_5_second_real_time_bar = {}

    def __str__(self):
        ans = 'Print models::Data::DataFromServer\n'
        for item in [self.tickPriceRecords, self.tickSizeRecords]:
            ans += '%s\n' % (item,)
        return ans[:-1]

    def set_tickInfoRecord(self, tickInfoRecord):
        if isinstance(tickInfoRecord, TickPriceRecord):
            self.tickPriceRecords.update(tickInfoRecord)
        elif isinstance(tickInfoRecord, TickSizeRecord):
            self.tickSizeRecords.update(tickInfoRecord)
        elif isinstance(tickInfoRecord, TickStringRecord):
            self.tickStringRecords.update(tickInfoRecord)
        elif isinstance(tickInfoRecord, TickOptionComputationRecord):
            self.tickOptionComputationRecords.update(tickInfoRecord)
        else:
            print(__name__ + '::set_tickInfoRecord: EXIT, cannot handle type=%s' % (type(tickInfoRecord, )))
            exit()

    def set_5_second_real_time_bar(self, str_security, aTime, price_open, price_high, price_low, price_close, volume,
                                   wap, count, timestamp):
        self.latest_5_second_real_time_bar[str_security] = {'time': aTime,
                                                            'open': price_open,
                                                            'high': price_high,
                                                            'low': price_low,
                                                            'close': price_close,
                                                            'volume': volume,
                                                            'wap': wap,
                                                            'count': count,
                                                            'timestamp': timestamp}

    def get_value(self, security, tickType, fieldName):
        # print(__name__ + '::get_value: security=%s tickType=%s fieldName=%s' % (security, tickType, fieldName))
        if tickType in [IBCpp.TickType.ASK, IBCpp.TickType.BID, IBCpp.TickType.LAST, IBCpp.TickType.OPEN,
                        IBCpp.TickType.HIGH, IBCpp.TickType.LOW, IBCpp.TickType.CLOSE]:
            return self.tickPriceRecords.get_value(security, tickType, fieldName)
        elif tickType in [IBCpp.TickType.VOLUME, IBCpp.TickType.BID_SIZE, IBCpp.TickType.ASK_SIZE,
                          IBCpp.TickType.LAST_SIZE]:
            return self.tickSizeRecords.get_value(security, tickType, fieldName)
        elif tickType in [IBCpp.TickType.ASK_OPTION_COMPUTATION, IBCpp.TickType.BID_OPTION_COMPUTATION,
                          IBCpp.TickType.LAST_OPTION_COMPUTATION, IBCpp.TickType.MODEL_OPTION]:
            return self.tickOptionComputationRecords.get_value(security, tickType, fieldName)
        elif tickType in [IBCpp.TickType.OPTION_CALL_OPEN_INTEREST, IBCpp.TickType.OPTION_PUT_OPEN_INTEREST]:
            return self.tickSizeRecords.get_value(security, tickType, fieldName)
        else:
            print(__name__ + '::get_value: EXIT, cannot handle tickType=%s' % (tickType,))
            exit()

    def get_5_second_real_time_bar(self, security):
        ans = self.latest_5_second_real_time_bar.get(security.full_print(), None)
        # print(f'{__name__}::get_5_second_real_time_bar: ans={ans}')
        return ans
