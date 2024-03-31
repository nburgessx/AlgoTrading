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

PROJECT = {
    'repBarFreq': 60  # handle_data function is automatically triggered every minute
}

TRADER = {
    'runMode': 'REGULAR'  # run handle_data continuously and regularly while ignoring market time.
}
def initialize(context):
    context.security = symbol('SPY')  # Define a security for the following part


# Refer to this Wiki page about Moving average crossover strategy
# https://en.wikipedia.org/wiki/Moving_average_crossover
def handle_data(context, data):
    # If today is not a trading day, just do not continue
    if not isTradingDay():
        return

    # The strategy run from 9:30 ~ 16:00 Eastern time.
    sTime = get_datetime('US/Eastern')
    hour = sTime.hour
    minute = sTime.miute
    if hour * 60 + minute >= 16 * 60:
        return
    if hour * 60 + minute < 9 * 60 + 30:
        return

    # if MA(5) > MA(60), then BUY the security if there is no order
    # Keep the long positions if there is a long position
    # if MA(5) < MA(60), clear the position
    hist = data.history(context.security, 'close', 80, '1m')  # fetch enough historical data to calculate Moving Average
    mv_5 = hist.rolling(5).mean()[-1]  # the latest fast moving average value
    mv_60 = hist.rolling(60).mean()[-1]  # the latest slow moving average value
    if mv_5 > mv_60:
        orderId = order_target_percent(context.security, 1.0)  # Place 100% of portfolio buy SPY
        order_status_monitor(orderId, target_status='Filled')
    else:
        orderId = order_target_percent(context.security, 0.0)  # Sell off all positions in my account
        order_status_monitor(orderId, target_status='Filled')
