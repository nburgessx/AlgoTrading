# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 10:40:03 2022

@author: JAY

# To Do
- Check output for all functions
- Parse outputs to pandas dataframe (historical data, all orders)
- Define place function order
- Define market data websockets

"""

import requests as rq
import json
import warnings
import pandas as pd
from pprint import pprint

warnings.filterwarnings('ignore')

BASE_URL = 'https://localhost:5000/v1/api'

portfolio_accounts_endpoint = '/portfolio/accounts'
historical_data_end_point = '/iserver/marketdata/history'
auth_status_end_point = '/iserver/auth/status'
tickle_end_point = '/tickle'
mds_end_point = '/iserver/marketdata/snapshot'
accounts_end_point = '/iserver/accounts'
account_pnl_end_point = '/iserver/account/pnl/partitioned'
orders_end_point = '/iserver/account/orders?force=false'

# Define unicodes for checkmark and cross to be printed on console
# Used only for cosmetics
cross_mark = '\u2A2F'
check_mark = '\u2713'

# Define time format
tf = '%Y%m%d %H:%M:%S'

def make_request(method, url, headers={}, payload={}, qs_params=None):
    
    try:
        if method == 'GET':
            
            raw_response = rq.get(url, headers=headers, data=payload,
                                  params=qs_params, verify=False)
            
        elif method == 'POST':
            
            raw_response = rq.post(url, headers=headers, data=payload,
                                   verify=False)
    except:
        raw_response = ''
        print(cross_mark + ' Not able to place requests!')
        
    return raw_response

def get_portfolio_accounts():
    """
    Doc: https://interactivebrokers.com/api/doc.html#tag/Account/paths/~1portfolio~1accounts/get
    """
    
    url = BASE_URL + portfolio_accounts_endpoint
    
    response = make_request('GET', url)
    
    parsed_res = json.loads(response.text)
    
    return response.status_code, parsed_res


def fetch_contract_details(conid):
    """
    Doc: https://interactivebrokers.com/api/doc.html#tag/Contract/paths/~1iserver~1contract~1{conid}~1info/get
    """
    
    end_point = '/iserver/contract/' + str(conid) + '/info'
    
    url = BASE_URL + end_point
    
    response = make_request('GET', url)
    
    res = json.loads(response.text)
    
    if response.status_code == 200:
        print(check_mark + ' Contract details fetched successfully.')
        print('INFO: Trading symbol is', res['symbol'])
    else:
        print(cross_mark + ' Issues in fetching contract details.')
        print(res)
        raise SystemExit(0)
    
    # return response.status_code, parsed_res


    
def fetch_historical_data(conid, exchange, period, bar, time_zone):
    """
    https://interactivebrokers.com/api/doc.html#tag/Market-Data/paths/~1iserver~1marketdata~1history/get
    """
    
    url = BASE_URL + historical_data_end_point
    
    params = {'conid':str(conid),
              'exchange':str(exchange),
              'period':str(period),
              'bar':str(bar)
              }
       
    response = make_request('GET', url, qs_params=params)
    
    res = json.loads(response.text)
    
    # Extract historical data from the response
    raw_historical_data = res['data']
    
    if len(raw_historical_data) == 0:
        print(cross_mark + ' No historical data available. Cannot Continue.')
        raise SystemExit(0)
    else:
        # Create an empty dataframe to hold historical data
        data = pd.DataFrame(columns=['o', 'h', 'c', 'l', 'v', 't'])
        
        # Append data to dataframe
        for bar in raw_historical_data:
            data = data.append(bar, ignore_index=True)
        
        # Convert epoch timestamps to human readable date time format
        data['t'] = pd.to_datetime(data['t'], unit='ms', utc=True)
    
        # Convert timezone
        data['t'] = data['t'].dt.tz_convert(time_zone)
        
        data['t'] = data['t'].dt.strftime(tf)
        
        # Set date as index
        data.set_index('t', drop=True, inplace=True)
        
        print(check_mark + ' Historical data downloaded successfully.')
        
        return data
    
    # return response.status_code, res

def auth_status(print_res=False):
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Session/paths/~1iserver~1auth~1status/post
    """
    
    url = BASE_URL + auth_status_end_point
    
    response = make_request('POST', url)
    
    if response.status_code == 200:
        
        res = json.loads(response.text)
        
        if res['authenticated'] == False:
            print(cross_mark + ' User not authenticated. Please log-in again.')
            print('Reason:', res['fail'])
            raise SystemExit(0)
        else:
            print(check_mark + ' User authentication status is true.')
    else:
        print(cross_mark + ' Not able to authenticate. Please log-in.')
        raise SystemExit(0)
        
    # return response.status_code, parsed_res

def tickle():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Session/paths/~1tickle/post
    """
    
    url = BASE_URL + tickle_end_point
    
    response = make_request('POST', url)
    
    res = json.loads(response.text)
    
    if response.status_code == 200:
        print(check_mark + ' Tickled the server successfully.')
    else:
        print(cross_mark + ' Tickling the server failed!')
        print('Response:')
        pprint(res)
    
    # return response.status_code, parsed_res

def fetch_ltp(conid):
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Market-Data/paths/~1iserver~1marketdata~1snapshot/get
    """
    
    url = BASE_URL + mds_end_point
    
    parameters = {'conids': conid}
    
    response = make_request('GET', url, qs_params=parameters)
    
    print('Status code:', response.status_code, '\n')
    
    parsed_res = json.loads(response.text)
    
    print(parsed_res)
    
    # if '31' in parsed_res[0].keys():
    #     last_price = parsed_res[0]['31']
    #     print('Last Price:', last_price)
        
    # if '_updated' in parsed_res[0].keys():
    #     last_time = parsed_res[0]['_updated']
    #     updated = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_time/1000))
    #     print('Updated on:', updated)

def fetch_accounts():
    
    url = BASE_URL + accounts_end_point
        
    response = make_request('GET', url)
    
    res = json.loads(response.text)
    
    if response.status_code == 200:
        print(check_mark + ' Account selected successfully.')
        print('INFO: Selected Account is', res['selectedAccount'])
    else:
        print(cross_mark + ' Cannot select the account.')
        print(cross_mark + ' Cannot start streaming data.')
        raise SystemExit(0)
    
    return True, res['selectedAccount']

def get_account_pnl():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/PnL/paths/~1iserver~1account~1pnl~1partitioned/get
    """
    
    url = BASE_URL + account_pnl_end_point
    
    response = make_request('GET', url)
    
    parsed_res = json.loads(response.text)
    
    return response.status_code, parsed_res

def get_portfolio_positions(account_id):
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Portfolio/paths/~1portfolio~1{accountId}~1positions~1{pageId}/get
    """
    
    end_point = 'portfolio/' + account_id + '/positions/0'
    
    url = BASE_URL + end_point
    
    response = make_request('GET', url)
    
    parsed_res = json.loads(response.text)
    
    return response.status_code, parsed_res
    
def get_positions_conid(conid):
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Portfolio/paths/~1portfolio~1positions~1{conid}/get
    """
    
    get_portfolio_accounts()
    
    end_point = 'portfolio/positions/' + conid
    
    url = BASE_URL + end_point
    
    response = make_request('GET', url)
    
    parsed_res = json.loads(response.text)
    
    return response.status_code, parsed_res

def get_orders():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Order/paths/~1iserver~1account~1orders/get
    """
    
    url = BASE_URL + orders_end_point
    
    response = make_request('GET', url)
    
    parsed_res = json.loads(response.text)
    
    print('## Response')
    pprint(parsed_res)
    
    return response.status_code, parsed_res

def place_orders(account_id, contract_id, o_type, o_side, o_quantity, price=0):
    
    end_point = '/iserver/account/' + account_id + '/orders'
    
    url = BASE_URL + end_point
    
    headers = {'Content-Type': 'application/json'}
    
    order_parameters = {'conid': contract_id,
                        'orderType': o_type,
                        'side': o_side,
                        'quantity': o_quantity,
                        'price': price,
                        'tif': 'DAY'}
    
    payload = {'orders':[order_parameters]}
    
    response = make_request('POST', url, 
                            headers=headers, 
                            payload=json.dumps(payload))
    
    if response.status_code == 200:
        
        print(check_mark + 'Market order placed.')
        
    else:
        
        print(cross_mark + ' Error in placing order.')
    
    print('## Response code:', response.status_code)
    
    print('## Response text:', json.loads(response.text))
        
        
    

#----------------x----------------x----------------x----------------x----------

# get_orders()

# fetch_accounts()

# fetch_contract_details(44652015)

# successful_req, msg = fetch_contract_details(173418084)
# successful_req, msg = get_portfolio_accounts()

# print(successful_req, msg)

# fetch_historical_data(conid=173418084, exchange='NSE', period='1d', bar='1min', outsideRth=False)

# successful_req, msg = auth_status()