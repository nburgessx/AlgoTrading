#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
    Title: The MACD divergence Strategy (NSE)
    Description: This is a long short strategy based on MACD technical indicators.
                 It is a simple and effective trend-following indicator.

                 The strategy uses:
                 - MACD = 26 day EMA of 'Close' - 12 day EMA of 'Close', and
                 signal = 9 day EMA of MACD
                 - The trading signals are generated using MACD and signal.

                 When MACD crosses above signal, we go long on the underlying security
                 When MACD crosses below signal, then we go short on it
    Style tags: Systematic Fundamental
    Asset class: Equities, Futures, ETFs and Currencies
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
from blueshift_library.technicals.indicators import macd
from blueshift.finance import commission, slippage
from blueshift.api import symbol, order_target_percent, set_commission, set_slippage


def initialize(context):
    """
        A function to define things to do at the start of the strategy
    """
    context.securities = [symbol('TATASTEEL')]
    context.params = {'indicator_lookback': 252, 'indicator_freq': '1d',
        'buy_signal_threshold': 0.5, 'sell_signal_threshold': -0.5,
        'trade_freq': 1, 'leverage': 1}
    context.bar_count = 0
    context.signals = dict((security, 0) for security in context.securities)
    context.target_position = dict((security, 0) for security in context.
        securities)
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.0))


def handle_data(context, data):
    """
        A function to define things to do at every bar
    """
    context.bar_count = context.bar_count + 1
    if context.bar_count < context.params['trade_freq']:
        return
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
    weight = round(1.0 / num_secs, 2) * context.params['leverage']
    for security in context.securities:
        if context.signals[security] > context.params['buy_signal_threshold']:
            context.target_position[security] = weight
        elif context.signals[security] < context.params['sell_signal_threshold'
            ]:
            context.target_position[security] = -weight
        else:
            context.target_position[security] = 0


def generate_signals(context, data):
    """
        A function to define define the signal generation
    """
    try:
        price_data = data.history(context.securities, 'close', context.
            params['indicator_lookback'], context.params['indicator_freq'])
    except:
        return
    for security in context.securities:
        px = price_data.loc[:, (security)].values
        context.signals[security] = signal_function(px, context.params)


def signal_function(px, params):
    """
        The main trading logic goes here, called by generate_signals above
    """
    macd_val, macdsignal, macdhist = macd(px, params['indicator_lookback'])
    if macd_val > macdsignal:
        return 1
    elif macd_val < macdsignal:
        return -1
    else:
        return 0

