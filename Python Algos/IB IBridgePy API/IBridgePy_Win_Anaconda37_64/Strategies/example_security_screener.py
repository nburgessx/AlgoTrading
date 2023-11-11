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
    response = get_scanner_results(instrument='STK',
                                   # scanCode='SCAN_socialSentimentNet_DESC',
                                   scanCode='MOST_ACTIVE',
                                   abovePrice=100.0,
                                   numberOfRows=10)
    print(response)
    for sec in response['security']:
        print(str(sec), show_real_time_price(sec, 'ask_price'))

    end()





