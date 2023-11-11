#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
    Title: Statistical Arbitrage using PCA
    Description: Sample pair-trading strategy using PCA
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
from blueshift_library.utils.utils import z_score
from sklearn.decomposition import PCA
import numpy as np
from blueshift.api import(symbol,
                        order_target_percent,
                        schedule_function,
                        date_rules,
                        time_rules
                        )


def initialize(context):
    """
        A function to define things to do at the start of the strategy
    """
    # universe selection
    context.x = symbol('AMBUJACEM')
    context.y = symbol('ACC')
    context.position = 0
    context.signal = 0
    context.hedge_ratio = 0

    # define strategy parameters
    context.params = {'indicator_lookback': 200,
                      'frequency': '1d',
                      'threshold': 0.8,
                      'leverage': 1}

    # Call strategy function every day at 10 AM
    schedule_function(statarb_pca_strategy,
                      date_rules.every_day(),
                      time_rules.market_open(minutes=30))


def statarb_pca_strategy(context, data):
    """
        A function to define the statistical arbitrage strategy logic using PCA
    """
    print("in statarb_pca_strategy")
    try:
        # Get the historic data for the stocks pair
        prices = data.history([context.x, context.y],
                              "close",
                              context.params['indicator_lookback'],
                              context.params['frequency']
                              )
        print("Got data!")
    except:
        print("Oops, no data!")
        return

    x = prices[context.x]
    y = prices[context.y]
    print(f"x is {x} and y is {y}")

    # Compute the z-scores of the prices of the two stocks
    zscore_x = z_score(x)
    zscore_y = z_score(y)

    print("Zscores of x and y are ", zscore_x, zscore_y)

    # calculate the signal based on the zcores of the two stocks
    context.signal = zscore_x - zscore_y
    print(f"Context signal is {context.signal}")

    if context.position == 0:
        context.hedge_ratio = hedgeratio_pca(x, y)

    # Long Entry
    if context.position == 0 and context.signal < -context.params['threshold']:
        print("Long Entry")
        context.position = 1

    # Long exit
    elif context.position > 0 and context.signal > 0:
        print("Long exit")
        context.position = 0

    # Short Entry
    if context.position == 0 and context.signal > context.params['threshold']:
        print("Short Entry")
        context.position = -1

    elif context.position < 0 and context.signal < 0:
        print("Short Exit")
        context.position = 0

    # Place orders as per the signal generated
    weight = context.position*context.params['leverage']/2

    # send fresh orders
    order_target_percent(context.x, -weight*context.hedge_ratio)
    order_target_percent(context.y, weight)


def hedgeratio_pca(x, y):
    print("Entered hedgeratio_pca")
    pca = PCA(1).fit(np.array([x, y]).T)
    print("PCA components ", pca.components_)
    hedge_ratio = pca.components_[0, 1]/pca.components_[0, 0]
    print("Hedge ratio based on PCA is ", hedge_ratio)
    return hedge_ratio

