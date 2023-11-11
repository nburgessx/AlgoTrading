# coding=utf-8
from sys import exit


class OrderStyle(object):
    def __init__(self, orderType,
                 limit_price=None,  # default price is None to avoid any mis-formatted numbers
                 stop_price=None,
                 trailing_amount=None,
                 trailing_percent=None,
                 limit_offset=None,
                 tif='DAY'):
        self.orderType = orderType
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.trailing_amount = trailing_amount
        self.trailing_percent = trailing_percent
        self.limit_offset = limit_offset
        self.tif = tif

    def __str__(self):
        string_output = ''
        if self.orderType == 'MKT':
            string_output = 'MarketOrder,unknown exec price'
        elif self.orderType == 'MOC':
            string_output = 'MarketOrder,unknown exec price'
        elif self.orderType == 'STP':
            string_output = 'StopOrder, stop_price=' + str(self.stop_price)
        elif self.orderType == 'LMT':
            string_output = 'LimitOrder, limit_price=' + str(self.limit_price)
        elif self.orderType == 'STP LMT':
            string_output = 'StopLimitOrder, stop_price=%s limit_price=%s' % (self.stop_price, self.limit_price)
        elif self.orderType == 'TRAIL LIMIT':
            if self.trailing_amount is not None:
                string_output = 'TrailStopLimitOrder, stop_price=' + str(self.stop_price) \
                                + ' trailing_amount=' + str(self.trailing_amount) \
                                + ' limit_offset=' + str(self.limit_offset)
            if self.trailing_percent is not None:
                string_output = 'TrailStopLimitOrder, stop_price=' + str(self.stop_price) \
                                + ' trailing_percent=' + str(self.trailing_percent) \
                                + ' limit_offset=' + str(self.limit_offset)
        elif self.orderType == 'TRAIL':
            string_output = 'TrailStopLimitOrder:'
            if self.trailing_amount is not None:
                string_output += ' trailing_amount=%s' % (self.trailing_amount,)
            if self.trailing_percent is not None:
                string_output += ' trailing_percent=%s' % (self.trailing_percent,)
            if self.stop_price is not None:
                string_output += ' stop_price=%s' % (self.stop_price,)
        else:
            print(__name__ + '::OrderStyle:EXIT, cannot handle orderType=%s' % (self.orderType,))
            exit()
        return string_output


class MarketOrder(OrderStyle):
    def __init__(self, tif='DAY'):
        OrderStyle.__init__(self, orderType='MKT', tif=tif)


class StopOrder(OrderStyle):
    def __init__(self, stop_price, tif='DAY'):
        OrderStyle.__init__(self, orderType='STP', stop_price=stop_price, tif=tif)


class LimitOrder(OrderStyle):
    def __init__(self, limit_price, tif='DAY'):
        OrderStyle.__init__(self, orderType='LMT', limit_price=limit_price, tif=tif)


class StopLimitOrder(OrderStyle):
    def __init__(self, limit_price, stop_price, tif='DAY'):
        OrderStyle.__init__(self, orderType='STP LMT', limit_price=limit_price, stop_price=stop_price, tif=tif)


class TrailStopLimitOrder(OrderStyle):
    def __init__(self, stop_price, limit_offset, trailing_amount=None, trailing_percent=None, tif='DAY'):
        OrderStyle.__init__(self, orderType='TRAIL LIMIT',
                            stop_price=stop_price,
                            limit_offset=limit_offset,
                            # either limit_offset or limit_price, NOT BOTH, IBridgePy chooses to set limit_offset
                            trailing_amount=trailing_amount,
                            # User sets either trailing_amount or tailing_percent, NOT BOTH
                            trailing_percent=trailing_percent,
                            # User sets either trailing_amount or tailing_percent, NOT BOTH
                            tif=tif)


class TrailStopOrder(OrderStyle):
    def __init__(self, stop_price=None, trailing_amount=None, trailing_percent=None, tif='DAY'):
        OrderStyle.__init__(self, orderType='TRAIL',
                            stop_price=stop_price,
                            trailing_amount=trailing_amount,
                            # User sets either trailing_amount or tailing_percent, NOT BOTH
                            trailing_percent=trailing_percent,
                            # User sets either trailing_amount or tailing_percent, NOT BOTH
                            tif=tif)


class LimitOnCloseOrder(OrderStyle):
    def __init__(self, limit_price):
        OrderStyle.__init__(self, orderType='LOC', limit_price=limit_price)


class LimitOnOpenOrder(OrderStyle):
    def __init__(self, limit_price):
        OrderStyle.__init__(self, orderType='LOO', limit_price=limit_price)


class MarketOnCloseOrder(OrderStyle):
    def __init__(self):
        OrderStyle.__init__(self, orderType='MOC')
