# coding=utf-8
import datetime as dt
import json
from sys import exit

import requests

from BasicPyLib.retrying import retry
from broker_client_factory.TdAmeritrade import auth
from .urls import ACCOUNTS, INSTRUMENTS, QUOTES, SEARCH, HISTORY, OPTIONCHAIN, MOVERS


class TDClient(object):
    def __init__(self, refresh_token, apiKey, refresh_token_createdOn, accountIds=None, log=None):
        self._log = log
        self._refresh_token = refresh_token
        self._refresh_token_createdOn = refresh_token_createdOn
        self._td_client_id = apiKey

        self._access_token_timestamp = None
        self._access_token = None
        self._renew_access_token()
        self.accountIds = accountIds or []

    def _is_access_token_valid(self):
        """
        access token is valid for 30 minutes only. It should be retrieved from TD server by a refresh token.
        The refresh token is valid for 90 days.
        :return: bool
        """
        if self._access_token is None:
            return False
        timeNow = dt.datetime.now()
        if self.get_TD_expiry_in_days() < 10:  # warning users if TD refresh token is about to expire.
            self._log.error('TD refresh token is about to expire on %s' % (self._refresh_token_createdOn + dt.timedelta(days=90),))
            self._log.error('Hint: Refer to Youtube video to get a new refresh token https://youtu.be/aT1nB-vMqdE')
        return (timeNow - self._access_token_timestamp).total_seconds() < 1800

    def get_TD_expiry_in_days(self):
        # as of 20201022, TD's access token expires in 90 days
        return 90 - (dt.date.today() - self._refresh_token_createdOn).days

    def _is_refresh_token_valid(self):
        return self.get_TD_expiry_in_days() >= 0

    def _renew_access_token(self):
        if not self._is_access_token_valid():
            if self._is_refresh_token_valid():
                self._access_token = auth.retrieve_access_token(self._refresh_token, self._td_client_id)
                self._access_token_timestamp = dt.datetime.now()
            else:
                self._log.error('TD refresh token has expired.')
                self._log.error('Hint: Refer to Youtube video to get a new refresh token https://youtu.be/aT1nB-vMqdE')
                exit()

    def get_new_refresh_token(self):
        return auth.renew_refresh_token(self._refresh_token, self._td_client_id)

    def _headers(self, mode=None):
        ans = {'Authorization': 'Bearer ' + self._access_token}
        if mode == 'json':
            ans['Content-type'] = 'application/json'
        return ans

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def accounts(self, positions=False, orders=False):
        self._renew_access_token()
        ret = {}

        if positions or orders:
            fields = '?fields='
            if positions:
                fields += 'positions'
                if orders:
                    fields += ',orders'
            elif orders:
                fields += 'orders'
        else:
            fields = ''

        if self.accountIds:
            for acc in self.accountIds:
                resp = requests.get(ACCOUNTS + str(acc) + fields, headers=self._headers())
                if resp.status_code == 200:
                    ret[acc] = resp.json()
                else:
                    # This error happened during weekends.
                    # ErrorCode=503 External service is unavailable. The associated error referenceID is be81f7fd-a48c-49b3-86c2-715392cbba87-07
                    raise Exception('ErrorCode=%s errorMessage=%s' % (resp.status_code, resp.text))
        else:
            resp = requests.get(ACCOUNTS + fields, headers=self._headers())
            if resp.status_code == 200:
                for account in resp.json():
                    ret[account['securitiesAccount']['accountId']] = account
            else:
                raise Exception(resp.text)
        return ret

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def search(self, symbol, projection='symbol-search'):
        self._renew_access_token()
        response = requests.get(SEARCH,
                                headers=self._headers(),
                                params={'symbol': symbol,
                                        'projection': projection})
        response.raise_for_status()
        return response.json()

    def fundamental(self, symbol):
        self._renew_access_token()
        return self.search(symbol, 'fundamental')

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def instrument(self, cusip):
        self._renew_access_token()
        response = requests.get(INSTRUMENTS + str(cusip), headers=self._headers())
        response.raise_for_status()
        return response.json()

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def quote(self, symbols):
        self._renew_access_token()
        response = requests.get(QUOTES,
                                headers=self._headers(),
                                params={'symbol': symbols.upper()})
        response.raise_for_status()
        return response.json()

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def history(self, symbol, **kwargs):
        self._renew_access_token()
        response = requests.get(HISTORY % symbol,
                                headers=self._headers(),
                                params=kwargs)
        response.raise_for_status()
        return response.json()

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def options(self, symbol, **kwargs):
        self._renew_access_token()
        dic = kwargs
        dic['symbol'] = symbol.upper()

        response = requests.get(OPTIONCHAIN,
                                headers=self._headers(),
                                params=dic)
        response.raise_for_status()
        return response.json()

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def movers(self, index, direction='up', change_type='percent'):
        self._renew_access_token()
        response = requests.get(MOVERS % index,
                                headers=self._headers(),
                                params={'direction': direction,
                                        'change_type': change_type})
        response.raise_for_status()
        return response.json()

    # DO NOT RETRY on placing order. It is too dangerous.
    def place_orders(self, account_id, order):
        self._renew_access_token()
        # Occasional, a float of price converts to json string and the precision was wrong. For example, 98.99 ->98.9900000000001
        # and the order is rejected by TD.
        # The issue is solved by forcing float to string in broker_client_factory::TdAmeritrade::client:: order_stop_price, order_limit_price, order_leg_price
        response = requests.post(ACCOUNTS + account_id + "/orders", headers=self._headers(mode='json'),
                                 data=json.dumps(order))
        if response.status_code == 201:
            orderId = response.headers['Location'].split('/')[-1]
            return orderId
        elif response.status_code == 400:
            raise RuntimeError(response.content)
        else:
            self._log.error(__name__ + '::place_orders: EXIT, Place order failed. response=%s.\n'
                                       'Suggestion:\n'
                                       '1. Check if the limit price or stop price is too far away from the current price.\n'
                                       '2. Print all orders. Failure reason will price out if the order status is abnormal.\n'
                                       '3. Check if data of HTTP POST is correct by using TD webAPI. data=%s\n' % (response.content, json.dumps(order)))
            exit()

    # DO NOT RETRY. It is too dangerous.
    def cancel_order(self, account_id, order_id):
        self._renew_access_token()
        response = requests.delete(ACCOUNTS + account_id + '/orders/%s' % (order_id,), headers=self._headers())
        if response.status_code == 200:
            pass
        else:
            self._log.error(__name__ + '::cancel_order: EXIT, cancel_order failed. response=%s' % (response.content,))
            exit()

    @retry(stop_max_attempt_number=3, wait_fixed=2000)  # max try 3 times, and wait 2 seconds in between
    def get_order(self, account_id, order_id):
        self._renew_access_token()
        response = requests.get(ACCOUNTS + account_id + '/orders/%s' % (order_id,), headers=self._headers())
        response.raise_for_status()
        return response.json()
