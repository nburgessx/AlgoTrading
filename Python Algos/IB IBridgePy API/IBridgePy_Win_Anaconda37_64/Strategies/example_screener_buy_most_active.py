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
    pass


def handle_data(context, data):

    # The stock scanner to find the top 10 most active stocks with price higher than $100
    # The universe of the scanned stocks depends on your data subscription at Interactive Brokers.
    # For IB's data subscription, please refer to this YouTube tutorial https://youtu.be/JkyxLYD2RBk
    # For more detailed discussions about get_scanner_results, please refer to this YouTube tutorial https://youtu.be/0sU4R1fIN3Y
    response = get_scanner_results(instrument='STK',
                                   scanCode='MOST_ACTIVE',
                                   abovePrice=100.0,
                                   numberOfRows=10)

    print(response)
    # A sample of returned response, which is a pandas DataFrame with two columns:
    # int rank: from 0 to 9, the lower the rank number, the higher the rank. 0 = highest rank
    # security: a Security object. It can be used to place order.
    #        rank     security
    #    0     0  STK,SPY,USD
    #    1     1  STK,IWM,USD
    #    2     2  STK,LQD,USD
    #    3     3  STK,XLV,USD
    #    4     4  STK,AGG,USD
    #    5     5  STK,JNK,USD
    #    6     6  STK,GLD,USD
    #    7     7  STK,XLK,USD
    #    8     8  STK,XBI,USD
    #    9     9  STK,DIA,USD

    # Rebalance the portfolio based on the scanner results
    for security in response['security']:
        orderId = order_target_percent(security, 0.1)  # Hold 10% of portfolio for each stock from the scanner results
        order_status_monitor(orderId, target_status=['Filled', 'Submitted', 'PreSubmitted'])

    # After the orders are placed, display account details.
    display_all()
    end()





