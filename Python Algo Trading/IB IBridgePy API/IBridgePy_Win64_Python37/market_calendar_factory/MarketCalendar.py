# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 04:56:16 2018

@author: IBridgePy@gmail.com
"""
import datetime as dt

import numpy as np
import pandas as pd
from pandas.tseries.offsets import MonthEnd

import market_calendar_factory.market_calendar_lib as mcal
from BasicPyLib.BasicTools import convert_datetime_to_date
import pytz


class MarketCalendar(object):
    def __init__(self, marketName='NYSE'):
        self._marketCalendar = mcal.get_calendar(marketName)
        self._current_date = None  # a way to speed up by storing the last calculation
        self._isTradingDaySet = set()  # restore answers to speed up
        self._notTradingDaySet = set()  # restore answers to speed up
        self._marketOpenCloseTimeRecord = {}
        self._nthTradingDayOfMonthRecord = {}
        self._nthTradingDayOfWeekRecord = {}
        self._getValidDaysRecord = {}

    # override
    def isTradingDay(self, aDatetime):
        """
        Check if a datetime is a trading day based on marketName
        output:
            True: It is a trading day.
        """
        # print(__name__ + '::isTradingDay: %s' % (aDatetime,))
        aDate = convert_datetime_to_date(aDatetime)
        if aDate in self._isTradingDaySet:
            return True
        if aDate in self._notTradingDaySet:
            return False
        if np.is_busday(aDate):
            ans = not (np.datetime64(aDate) in self._marketCalendar.holidays().holidays)
        else:
            ans = False
        if ans:
            self._isTradingDaySet.add(aDate)
        else:
            self._notTradingDaySet.add(aDate)
        return ans

    def isEarlyClose(self, aDatetime):
        aDate = convert_datetime_to_date(aDatetime)
        if not self.isTradingDay(aDate):  # If it is NOT a trading day, definitely it is not an early close
            return False
        pdSeries = self.get_early_closes(aDate, aDate)['market_close']  # Only returns early closes
        aTimestamp = pd.Timestamp(aDate)
        if aTimestamp not in pdSeries.index:
            return False
        # Returned market_close_time does not have timezone. So, localize to UTC and convert to Eastern
        if not pdSeries[aTimestamp].tzinfo:
            return pdSeries[aTimestamp].tz_localize('UTC').tz_convert('US/Eastern').hour == 13  # Early close at 1:00PM
        else:
            return pdSeries[aTimestamp].tz_convert('US/Eastern').hour == 13  # Early close at 1:00PM

    def get_market_open_close_time(self, aDatetime):
        aDate = convert_datetime_to_date(aDatetime)
        if aDate in self._marketOpenCloseTimeRecord:
            opn, close = self._marketOpenCloseTimeRecord[aDate]
            return opn, close
        if self.isTradingDay(aDatetime):
            sch = self._marketCalendar.schedule(start_date=aDatetime, end_date=aDatetime)
            opn, close = sch.iloc[0]['market_open'], sch.iloc[0]['market_close']
            self._marketOpenCloseTimeRecord[aDate] = (opn, close)
            return opn, close
        else:
            return None, None

    def _get_validDays(self, startDate, endDate):
        if (startDate, endDate) in self._getValidDaysRecord:
            return self._getValidDaysRecord[(startDate, endDate)]
        ans = self._marketCalendar.valid_days(start_date=startDate, end_date=endDate)
        self._getValidDaysRecord[(startDate, endDate)] = ans
        return ans

    # noinspection DuplicatedCode
    def nth_trading_day_of_month(self, aDatetime):
        """
        1st trading day of month is 0
        last trading day of month is -1
        @param aDatetime: dt.date
        @result: list [nth trading day in a month, reverse location in a month]
        """
        aDay = convert_datetime_to_date(aDatetime)
        if aDay in self._nthTradingDayOfMonthRecord:
            return self._nthTradingDayOfMonthRecord[aDay]
        monthStartDate = aDay.replace(day=1)
        monthEndDate = (aDay + MonthEnd(0)).date()  # change pd.TimeStamp to dt.date
        ls_validDays = self._get_validDays(monthStartDate, monthEndDate)

        t = pd.Timestamp(aDay).tz_localize(pytz.utc)
        if t in ls_validDays:
            x = ls_validDays.get_loc(t)
            ans = [x, x - len(ls_validDays)]
            self._nthTradingDayOfMonthRecord[aDay] = ans
            return ans
        else:
            self._nthTradingDayOfMonthRecord[aDay] = None
            return None

    # noinspection DuplicatedCode
    def nth_trading_day_of_week(self, aDatetime):
        """
        1st trading day of week is 0
        last trading day of week is -1
        @param aDatetime: dt.date
        @result: list [nth trading day in a week, reverse location in a week]
        """
        aDay = convert_datetime_to_date(aDatetime)
        if aDay in self._nthTradingDayOfWeekRecord:
            return self._nthTradingDayOfWeekRecord[aDay]
        tmp = aDay.weekday()
        weekStartDate = aDay - dt.timedelta(days=tmp)
        weekEndDate = weekStartDate + dt.timedelta(days=4)
        ls_validDays = self._get_validDays(weekStartDate, weekEndDate)
        t = pd.Timestamp(aDay).tz_localize(pytz.utc)
        if t in ls_validDays:
            x = ls_validDays.get_loc(t)
            ans = [x, x - len(ls_validDays)]
            self._nthTradingDayOfWeekRecord[aDay] = ans
            return ans
        else:
            self._nthTradingDayOfWeekRecord[aDay] = None
            return None

    def get_params_of_a_daytime(self, dateTime):
        """
        return 4 parameters to fit IBridgePy requirements
            1. nth_trading_day_of_month, two int, for example [21,-1]
            2. nth_trading_day_of_week, two int, for example [3, -2]
            3. int the hour of the dayTime
            4. int the minute of the dayTime
        """
        return (self.nth_trading_day_of_month(dateTime),
                self.nth_trading_day_of_week(dateTime),
                dateTime.hour,
                dateTime.minute)

    def get_early_closes(self, start_date, end_date):
        sch = self._marketCalendar.schedule(start_date=start_date, end_date=end_date)
        return self._marketCalendar.early_closes(sch)

    def is_market_open_at_this_moment(self, aDatetime):
        if not self.isTradingDay(aDatetime):
            return False
        marketOpenTime, marketCloseTime = self.get_market_open_close_time(aDatetime)
        if (marketOpenTime is None) or (marketCloseTime is None):
            return False
        return marketOpenTime <= aDatetime < marketCloseTime
