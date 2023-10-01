# -*- coding: utf-8 -*-
"""
Created on Sun, 1st October 2023

@author: Nicholas Burgess

@documentation: https://interactivebrokers.github.io/cpwebapi/index.html
"""

from web_api_functions import fetch_historical_data, fetch_ltp, fetch_accounts, get_account_pnl
from web_api_functions import authentication_status, reauthenticate, get_portfolio_positions
from web_api_functions import fetch_contract_details, get_positions_conid, get_orders
from web_api_functions import place_orders, validate_sso, logout

authentication_status()

fetch_accounts()

fetch_contract_details('44652015')

fetch_ltp()

fetch_historical_data()

res = place_orders('DU2966568')

get_orders()

get_portfolio_positions('DU2966568')

get_positions_conid('44652015')

get_account_pnl()

validate_sso()

reauthenticate()

logout()


















