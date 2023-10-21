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


def initialize(context):
    context.run_once = False  # To show if the handle_data has been run in a day
    context.security = symbol('SPY')  # Define a security for the following part

# Refer to this Wiki page about Moving average crossover strategy
# https://en.wikipedia.org/wiki/Moving_average_crossover
def handle_data(context, data):
    # sTime is the IB server time.
    # get_datetime() is the build-in function to obtain IB server time
    sTime = get_datetime('US/Eastern')

    if sTime.weekday() <= 4: # Only trade from Mondays to Fridays

        # 2 minutes before the market closes, reset the flag
        # get ready to trade
        if sTime.hour == 15 and sTime.minute == 58 and context.run_once is True:
            context.run_once = False

        # 1 minute before the market closes, do moving average calculation
        # if MA(5) > MA(60), then BUY the security if there is no order
        # Keep the long positions if there is a long position
        # if MA(5) < MA(60), clear the position
        if sTime.hour == 15 and sTime.minute == 59 and context.run_once is False:
            hist = data.history(context.security, 'close', 80, '1d')  # fetch enough historical data to calculate Moving Average
            mv_5 = hist.rolling(5).mean()[-1]  # the latest fast moving average value
            mv_60 = hist.rolling(60).mean()[-1]  # the latest slow moving average value
            if mv_5 > mv_60:
                orderId = order_target_percent(context.security, 1.0)  # Place 100% of portfolio buy SPY
                order_status_monitor(orderId, target_status='Filled')
            else:
                orderId = order_target_percent(context.security, 0.0)  # Sell off all positions in my account
                order_status_monitor(orderId, target_status='Filled')
            context.run_once = True
