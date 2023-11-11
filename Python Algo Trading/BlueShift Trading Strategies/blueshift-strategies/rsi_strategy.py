#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
    Title: Relative Strength Indicator (RSI) Strategy (NSE)
    Description: This is a long short strategy based on 14 day RSI index. 
    If RSI > 70, Sell the  shares
    If RSI < 30, Buy the shares
    Dataset: NSE
    
    ######
    Disclaimer: All investments and trading in the stock market involve risk. Any 
    decisions to place trades in the financial markets, including trading in stock or
    options or other financial instruments is a personal decision that should only be 
    made after thorough research, including a personal risk and financial assessment and
    the engagement of professional assistance to the extent you believe necessary. 
    The trading strategies or related information mentioned in this article is for 
    informational purposes only.
    ######
"""
from blueshift_library.technicals.indicators import rsi
from blueshift.finance import commission, slippage
from blueshift.api import(symbol,
                        order_target_percent,
                        set_commission,
                        set_slippage
                        )


def initialize(context):
    """
        A function to define things to do at the start of the strategy
    """
    # universe selection
    context.securities = [symbol('TATASTEEL'), symbol('RELIANCE')]

    # define strategy parameters
    context.params = {'indicator_lookback': 90,
                      'indicator_freq': '1d',
                      'rsi_period': 14,
                      'trade_freq': 1,
                      'leverage': 1}

    # variable to control trading frequency
    context.bar_count = 0

    # variables to track signals and target portfolio
    context.signals = dict((security, 0) for security in context.securities)
    context.target_position = dict((security, 0)
                                   for security in context.securities)

    # set trading cost and slippage to zero
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.00))


def handle_data(context, data):
    """
        A function to define things to do at every bar
    """
    context.bar_count = context.bar_count + 1
    if context.bar_count < context.params['trade_freq']:
        return

    # time to trade, call the strategy function
    context.bar_count = 0
    run_strategy(context, data)


def run_strategy(context, data):
    """
        A function to define core strategy steps
    """
    generate_signals(context, data)
    generate_target_position(context, data)
    rebalance(context, data)


def rebalance(context, data):
    """
        A function to rebalance - all execution logic goes here
    """
    for security in context.securities:
        order_target_percent(security, context.target_position[security])


def generate_target_position(context, data):
    """
        A function to define target portfolio
    """
    num_secs = len(context.securities)
    weight = round(1.0/num_secs, 2)*context.params['leverage']

    for security in context.securities:
        if context.signals[security] == 1:
            context.target_position[security] = weight
        elif context.signals[security] == -1:
            context.target_position[security] = -weight
        else:
            context.target_position[security] = 0


def generate_signals(context, data):
    """
        A function to define define the signal generation
    """
    try:
        price_data = data.history(context.securities, 'close',
                                  context.params['indicator_lookback'],
                                  context.params['indicator_freq'])
    except:
        return

    for security in context.securities:
        px = price_data.loc[:, security].values
        context.signals[security] = signal_function(px, context.params)


def signal_function(px, params):
    """
        The main trading logic goes here, called by generate_signals above
    """
    rsi_val = rsi(px, params['rsi_period'])

    if rsi_val < 30:
        return 1
    elif rsi_val > 70:
        return -1
    else:
        return 0

