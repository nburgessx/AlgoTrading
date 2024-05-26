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

from configuration import run_me_at_td_ameritrade

fileName = 'example_show_positions.py'
# fileName = 'example_get_historical_data.py'
# fileName = 'example_show_real_time_prices.py'
# fileName = 'example_place_order.py'

# To trade with TD Ameritrade using IBridgePy. Refer to YouTube tutorial https://youtu.be/uI0CfX2ePD0
# Step 1. Create an API key. Refer to YouTube tutorial https://youtu.be/l3qBYMN4yMs
# Step 2. Get a refresh token
#       Option a: Get a refresh token for Windows users YouTube tutorial https://youtu.be/Ql6VnR0GIYY
#       Option b: Get a refresh token without any coding YouTube tutorial https://youtu.be/aT1nB-vMqdE
# Step 3: Put the API Key and the refresh token in setting.py YouTube tutorial https://youtu.be/9hFZmCe7d4Q
# Step 4: Input your TD account code
# Step 5: Choose a fileName and run!
# If you need help on coding, please consider our well known Rent-a-Coder service. https://ibridgepy.com/rent-a-coder/

accountCode = '12345678'  # Input your TD account code/number here. It is NOT the account login ID.

run_me_at_td_ameritrade(fileName, globals())
