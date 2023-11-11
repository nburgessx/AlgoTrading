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
from configuration import run_me

fileName = 'example_show_positions.py'
# fileName = 'example_get_historical_data.py'
# fileName = 'example_show_real_time_prices.py'
# fileName = 'example_place_order.py'
# fileName = 'example_get_contract_details.py'
# fileName = 'example_get_option_info.py'
# fileName = 'example_security_screener.py'

# To trade with Interactive Brokers using IBridgePy.
# Instruction for Mac users. Refer to YouTube tutorial https://youtu.be/M96ZPXQnngA
# Instruction for Windows users. Refer to YouTube tutorial https://youtu.be/ywaZiGFrcrc
#
# Step 1. Config Trader Workstation TWS or Gateway. Refer to YouTube tutorial https://youtu.be/9hPOB-tY5vk
# Step 2. Change accountCode. Login ID is not accountCode
# Step 3. Config IBridgePy. Refer to YouTube tutorial https://youtu.be/9hFZmCe7d4Q
#      For example, a) config handle_data( ) to run every 3 minutes
#                   b) run like Quantopian mode
#                   c) logLevel
#                   d) run before market open
#                   e) others
# Step 4: Choose a fileName and run !
# If you need help on coding, please consider our well known Rent-a-Coder service. https://ibridgepy.com/rent-a-coder/


# !!!!!! IMPORTANT  !!!!!!!!!!!!!!!!!
accountCode = 'DU1868499'  # You need to change it to your own IB account number
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

'''
In the default mode, handle_data will be called every second.
To run Quantopian algorithms, handle_data will be called every minute
Please use the following runMode
'''
# runMode = 'RUN_LIKE_QUANTOPIAN'

run_me(fileName, globals())