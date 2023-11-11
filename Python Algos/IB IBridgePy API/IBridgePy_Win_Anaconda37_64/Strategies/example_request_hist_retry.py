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
import pytz
import time


def retry_request_historical_data(context, data):
    """
    request_historical_data may not get responses from brokers' data server for many reasons.
    Added retry logic to handle RuntimeError
    """
    retry = 3  # Retry 3 times and give up
    count = 1  # The number of the current try
    ans = None  # Retrieved hist if the action is successful.
    while count <= retry:
        count += 1
        try:
            # Invoke request_historical_data to retrieve historical data from server
            ans = request_historical_data(context.sec, '1 Day', '5 D', endTime=pytz.utc.localize(dt.datetime.utcnow()))
            break
        except RuntimeError:
            # Sleep 3 seconds and try it again
            time.sleep(3)
    return ans


def initialize(context):
    context.sec = symbol('SPY')


def handle_data(context, data):
    hist = retry_request_historical_data(context, data)
    print(hist)
    end()
