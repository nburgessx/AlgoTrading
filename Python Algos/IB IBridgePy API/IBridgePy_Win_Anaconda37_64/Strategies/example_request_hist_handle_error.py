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
import os


def initialize(context):
    context.secList = symbols('XLE', 'BAD_SYMBOL', 'SPY')


def handle_data(context, data):
    """
    Download historical data of a list of symbols and save them to local files while gracefully handle errors.
    Please refer to this YouTube tutorial: https://youtu.be/Vuf7Jb9-hCk
    """
    for security in context.secList:
        try:
            # Request historical data and it will fail on the 'BAD_SYMBOL' because it is not a real symbol.
            # When it fails, the error will be caught by the 'except' block.
            hist = request_historical_data(security, '1 day', '5 D')

            # Prepare a file name for each symbol
            filePath = os.path.join(os.getcwd(), str(security) + '_1day_5D.csv')
            print(filePath)
            hist.to_csv(filePath)  # Save pandas DataFrame to local file.
        except RuntimeError:
            print(str(security), 'failed')
    end()
