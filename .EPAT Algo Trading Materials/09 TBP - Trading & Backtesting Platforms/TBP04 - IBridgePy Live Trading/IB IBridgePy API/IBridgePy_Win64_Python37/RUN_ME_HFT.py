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

from configuration import run_me_at_HFT

fileName = 'example_show_real_time_prices.py'

accountCode = 'DU1868499'

PROJECT = {
    'repBarFreq': 0.25,  # unit is second. handle_data function will be invoked 4 times in a second.
}

run_me_at_HFT(fileName, globals())
