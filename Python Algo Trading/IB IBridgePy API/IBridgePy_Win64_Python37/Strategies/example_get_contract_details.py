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
    # !!! IBridgePy will error out if the amount of returned results are too many and it takes more than 30 seconds

    # The return is a dict, keyed by field names
    # {
    # 'primaryExchange': 'ARCA',
    # 'validExchanges': 'SMART,AMEX,NYSE,CHX,ARCA,ISLAND,DRCTEDGE,NSX,BEX,BATS,EDGEA,BYX,PSX'
    # }
    print(get_contract_details(secType='STK', symbol='SPY', field=['primaryExchange', 'validExchanges']))

    # The expected return is a pandas dataframe,
    # Columns include contractName, contract, security object, expiry, strike, right, multiplier
    print(get_contract_details(secType='OPT', symbol='ES', field='summary',
                               currency='USD', exchange='CBOE', primaryExchange='CBOE',
                               right='C'))
    end()