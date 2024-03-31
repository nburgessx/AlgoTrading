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

# This code can be back tested at Quantopian


def initialize(context):
    context.security = symbol('SPY') # Define a security, SP500 ETF

    # schedule_function is an IBridgePy function, also supported by Quantopian
    # date_rules.every_day : the dailyFunc will be run on every business day
    # time_rules.market_close(minutes=1) : the time to run dailyFunc is
    # 1 minute before U.S. market close (15:59:00 US/Eastern time)
    schedule_function(dailyFunc, date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_close(minutes=1))


def dailyFunc(context, data):
    print('dailyFunc', get_datetime())
    # dailyFunc is scheduled by schedule_function
    # It will run at 15:59:00 US/Eastern time on every business day
    # 1 minute before U.S. market close.
    hist = request_historical_data(context.security, '1 day', '2 D')
    close_yesterday = hist['close'][-2]
    close_today = hist['close'][-1]
    if close_today > close_yesterday:
        order_target_percent(context.security, 0.0)
    else:
        order_target_percent(context.security, 1.0)
