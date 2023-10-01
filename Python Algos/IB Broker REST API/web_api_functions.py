# -*- coding: utf-8 -*-
"""
Created on Sun, 1st October 2023

@author: Nicholas Burgess

@documentation: https://www.interactivebrokers.com/api/doc.html
"""

# Import necessary libraries
import requests
from pprint import pprint
import warnings
import json
import pandas as pd
import time

# Ignore warnings
warnings.filterwarnings(action='ignore')

def authentication_status():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Session/paths/~1iserver~1auth~1status/post
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to check authentication status
    end_point = 'iserver/auth/status'
    
    # Create a URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define parameters
    payload={}
    
    # Request data
    response = requests.post(url, headers=headers, data=payload, verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)
    
def validate_sso():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Session/paths/~1sso~1validate/get
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to validate sso
    end_point = 'sso/validate'
    
    # Create a URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define parameters
    payload={}
    
    # Request data
    response = requests.get(url, headers=headers, data=payload, verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)

def logout():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Session/paths/~1logout/post
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to end the current session
    end_point = 'logout'
    
    # Create a URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define parameters
    payload={}
    
    # Request data
    response = requests.post(url, headers=headers, data=payload, verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)

def reauthenticate():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Session/paths/~1iserver~1reauthenticate/post
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to reauthenticate the user
    end_point = 'iserver/reauthenticate'
    
    # Create a URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define parameters
    payload={}
    
    # Request data
    response = requests.post(url, headers=headers, data=payload, verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)
    
def tickle():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Session/paths/~1tickle/post
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint for keeping server connection alive
    end_point = 'tickle'
    
    # Create a URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define payload
    payload={}
    
    # Request data
    response = requests.post(url, headers=headers, data=payload, verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)
    
def fetch_contract_details(conid):
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Contract/paths/~1iserver~1contract~1{conid}~1info/get
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to fetch contract details
    end_point = 'iserver/contract/' + conid + '/info'
    
    # Create a URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define parameters
    payload={}
    
    # Request data
    response = requests.get(url, headers=headers, data=payload, verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)

def fetch_historical_data():
    """
    Documentation link: https://www.interactivebrokers.com/api/doc.html#tag/Market-Data/paths/~1iserver~1marketdata~1history/get

    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint
    end_point = 'iserver/marketdata/history'
    
    # Create a URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define payload
    payload = {}
    
    parameters = {'conid': '173418084',
                  'exchange': 'NSE',
                  'period': '1d',
                  'bar': '1min'
                  }
    
    # Request data
    response = requests.get(url, 
                            headers=headers, 
                            data=payload, 
                            params=parameters,
                            verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Extract historical data from the responsse
    historical_data= parsed_res['data']
    
    # Create an empty dataframe to hold historical data
    data = pd.DataFrame(columns=['o', 'h', 'c', 'l', 'v', 't'])
    
    # Append data to dataframe
    for bar in historical_data:
        data = data.append(bar, ignore_index=True)
    else:
        print('Data stored in dataframe.')
    
    # Convert epoch timestamps to human readable date time format
    data['t'] = pd.to_datetime(data['t'], unit='ms', utc=True)

    # Convert timezone
    data['t'] = data['t'].dt.tz_convert('Asia/Kolkata')
    
    # Set date as index
    data.set_index('t', drop=True, inplace=True)
    
    print(data)
    
    print('*' * 50)

def fetch_snapshot_data():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Market-Data/paths/~1iserver~1marketdata~1snapshot/get
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint for fetching snapshot data
    end_point = 'iserver/marketdata/snapshot'
    
    # Create an URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define the payload
    payload = {}
    
    # Define parameters
    parameters = {
        'conids': 44652015
        }
    
    # Request data
    response = requests.get(url, 
                            headers=headers, 
                            data=payload, 
                            params=parameters,
                            verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    print(parsed_res)
    
    if '31' in parsed_res[0].keys():
        last_price = parsed_res[0]['31']
        print('Last Price:', last_price)
        
    if '_updated' in parsed_res[0].keys():
        last_time = parsed_res[0]['_updated']
        updated = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_time/1000))
        print('Updated on:', updated)
    
    print('*' * 50)

def fetch_accounts():
    """
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint for fetching accounts
    end_point = 'iserver/accounts'
    
    # Create an URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define the payload
    payload = {}
    
    # Send request
    response = requests.get(url,
                            headers=headers,
                            data=payload,
                            verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
   
    pprint(parsed_res)
    
    print('*' * 50)
    
def get_account_pnl():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/PnL/paths/~1iserver~1account~1pnl~1partitioned/get
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to fetch account pnl
    end_point = 'iserver/account/pnl/partitioned'
    
    # Create an URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define parameters
    payload={}
    
    # Request data
    response = requests.get(url, 
                             headers=headers, 
                             data=payload, verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)

def get_portfolio_positions(account_id):
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Portfolio/paths/~1portfolio~1{accountId}~1positions~1{pageId}/get
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to fetch positions
    end_point = 'portfolio/' + account_id + '/positions/0'
    
    # Create an URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define parameters
    payload = {}
    
    # Request data
    response = requests.get(url,
                            headers=headers,
                            data=payload, verify=False)

    # Print status code
    print('Status Code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)

def get_portfolio_accounts():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Account/paths/~1portfolio~1accounts/get
    """
    
    base_url = 'https://localhost:5000/v1/api/'
    end_point = 'portfolio/accounts/'
    
    url = base_url + end_point
    
    headers = {}
    
    payload={}
    
    response = requests.get(url, headers=headers, data=payload, verify=False)
    
    print('Status code:', response.status_code, '\n')
    parsed_res = json.loads(response.text)
    
    pprint(parsed_res)
    
    print('*' * 50)
    
def get_positions_conid(conid):
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Portfolio/paths/~1portfolio~1positions~1{conid}/get
    """
    
    get_portfolio_accounts()
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to fetch positions by contract id
    end_point = 'portfolio/positions/' + conid
    
    # Create a URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define parameters
    payload={}
    
    # Request data
    response = requests.get(url, headers=headers, data=payload, verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)
    
def get_orders():
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Order/paths/~1iserver~1account~1orders/get
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to fetch all orders
    end_point = 'iserver/account/orders'
    
    # Create a URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {}
    
    # Define payload
    payload={}
    
    # Request data
    response = requests.get(url, headers=headers, data=payload, verify=False)
    
    # Print status code
    print('Status code:', response.status_code, '\n')
    
    # Parse the response
    parsed_res = json.loads(response.text)
    
    # Prints the response
    pprint(parsed_res)
    
    print('*' * 50)
    
def place_orders(account_id):
    """
    https://www.interactivebrokers.com/api/doc.html#tag/Order/paths/~1iserver~1account~1{accountId}~1orders/post
    """
    
    # Define the base url
    base_url = 'https://localhost:5000/v1/api/'
    
    # Define an endpoint to place orders
    end_point = 'iserver/account/' + account_id + '/orders'
    
    # Create an URL
    url = base_url + end_point
    
    # Print the URL
    print('URL:', url, '\n')
    
    # Define headers
    headers = {'Content-Type': 'application/json'}
    
    # Define order parameters
    order_parameters = {'acctId': account_id,
                        'conid': 56985419,
                        'secType': '56985419:STK',
                        'orderType': 'LMT',
                        'side': 'SELL',
                        'tif': 'DAY',
                        'price': 1458.60,
                        'quantity': 30,
                        'ticker': 'COLPAL',
                        'cOID': 'my-sell-order',
                        'useAdaptive': True,
                        'isCcyConv': False,
                        'outsideRTH': False
                        
        }
    
    # Define payload
    payload = {'orders':[order_parameters]}
    
    # Place order
    response = requests.post(url, 
                             headers=headers,
                             data=json.dumps(payload), 
                             verify=False)
    
    # Print the status code
    print('Status Code:', response.status_code, '\n')
    
    return response    