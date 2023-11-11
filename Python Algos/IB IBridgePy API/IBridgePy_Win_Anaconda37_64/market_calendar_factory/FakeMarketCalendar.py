# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 00:03:22 2018

@author: IBridgePy@gmail.com
"""


class FakeMarketCalendar:
    def __init__(self):
        pass

    # noinspection PyUnusedLocal
    @staticmethod
    def isTradingDay(timeNow):
        """
        return True if day is a trading day
        """
        return True

    @staticmethod
    def get_market_open_close_time(aDateTime):
        opn = aDateTime.replace(hour=0, minute=0, second=0)
        close = aDateTime.replace(hour=23, minute=59, second=59)
        return opn, close

    @staticmethod
    def nth_trading_day_of_month(aDay):
        return aDay.day, aDay.day - 30

    @staticmethod
    def nth_trading_day_of_week(aDay):
        return aDay.weekday(), aDay.weekday() - 7

    @staticmethod
    def is_market_open_at_this_moment(aDatetime):
        return True


if __name__ == '__main__':
    import datetime as dt
    c = FakeMarketCalendar()
    print(c.get_market_open_close_time(dt.datetime.now()))
