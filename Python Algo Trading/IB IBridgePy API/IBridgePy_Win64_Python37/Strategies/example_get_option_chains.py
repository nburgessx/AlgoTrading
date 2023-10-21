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
import datetime as dt

from IBridgePy.IbridgepyTools import closest_strike, closest_expiry


def initialize(context):
    pass


def handle_data(context, data):
    # Get the available option chains for AAPL (Apple Inc. options)
    # As an example, get all "Call" options of AAPL
    ans = get_contract_details(secType='OPT', symbol='AAPL', field='summary', currency='USD', exchange='CBOE', primaryExchange='CBOE', right='C')
    # The expected return is a pandas.DataFrame
    #                                security
    # 1288  OPT,AAPL,USD,20200904,465.0,C,100
    # 1289  OPT,AAPL,USD,20200904,470.0,C,100
    # 1290  OPT,AAPL,USD,20200904,475.0,C,100
    # 1291  OPT,AAPL,USD,20200904,480.0,C,100
    # 1292  OPT,AAPL,USD,20200904,485.0,C,100
    print(ans.tail())

    # There are so many options.
    # Filter the options which has an expiry closest to a target datetime.
    df_closest_expiry = closest_expiry(ans, dt.datetime.now())
    print(df_closest_expiry.tail())

    # Filter the options which has a strike price closest to a target strike price.
    df_closest_strike = closest_strike(df_closest_expiry, 450.0)
    print(df_closest_strike.tail())
    end()
