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

# Introduction to Security object. YouTube tutorial https://youtu.be/JkyxLYD2RBk
# Introduction to place orders. YouTube tutorial https://youtu.be/JkyxLYD2RBk
# If you need help on coding, please consider our well known Rent-a-Coder service. https://ibridgepy.com/rent-a-coder/

def initialize(context):
    context.flag = False
    context.security = symbol('SPY')


def handle_data(context, data):
    if not context.flag:
        # http://www.ibridgepy.com/ibridgepy-documentation/#order8212_similar_as_order_at_Quantopian
        orderId = order(context.security, 100)  # buy 100 shares of SPY

        # http://www.ibridgepy.com/ibridgepy-documentation/#order_status_monitor
        order_status_monitor(orderId, target_status=['Filled', 'Submitted', 'PreSubmitted'])
        context.flag = True
    else:
        display_all()
        end()
