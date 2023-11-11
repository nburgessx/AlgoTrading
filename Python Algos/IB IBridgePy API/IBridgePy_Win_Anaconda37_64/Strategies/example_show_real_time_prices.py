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
# Introduction to show real time prices. YouTube tutorial https://youtu.be/O_lNWAXMLHw
# If you need help on coding, please consider our well known Rent-a-Coder service. https://ibridgepy.com/rent-a-coder/

def initialize(context):
    context.security = symbol('SPY')


def handle_data(context, data):
    print (get_datetime().strftime("%Y-%m-%d %H:%M:%S %Z"))
    ask_price = show_real_time_price(context.security, 'ask_price')
    print ("SPY ask_price=", ask_price)

