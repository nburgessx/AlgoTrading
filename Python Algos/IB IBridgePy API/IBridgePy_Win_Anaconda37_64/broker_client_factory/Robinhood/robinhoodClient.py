from .Robinhood import Robinhood
import requests
# noinspection PyPep8Naming
import broker_client_factory.Robinhood.exceptions as RH_exception
from broker_client_factory.Robinhood import endpoints


def get_instrument_by_uuid(uuid):
    # {u'margin_initial_ratio': u'1.0000',
    #  u'rhs_tradability': u'untradable',
    #  u'id': u'7901e51e-35ad-4b50-8a77-09260388f984',
    #  u'market': u'https://api.robinhood.com/markets/XNAS/',
    #  u'simple_name': u'Taronis Technologies',
    #  u'min_tick_size': None,
    #  u'maintenance_ratio': u'1.0000',
    #  u'tradability': u'untradable',
    #  u'state': u'inactive',
    #  u'type': u'stock',
    #  u'tradeable': False,
    #  u'fundamentals': u'https://api.robinhood.com/fundamentals/TRNX/',
    #  u'quote': u'https://api.robinhood.com/quotes/TRNX/',
    #  u'symbol': u'TRNX',
    #  u'day_trade_ratio': u'1.0000',
    #  u'splits': u'https://api.robinhood.com/instruments/7901e51e-35ad-4b50-8a77-09260388f984/splits/',
    #  u'tradable_chain_id': None,
    #  u'name': u'Taronis Technologies, Inc. Common Stock',
    #  u'url': u'https://api.robinhood.com/instruments/7901e51e-35ad-4b50-8a77-09260388f984/',
    #  u'country': u'US',
    #  u'bloomberg_unique': u'EQ0000000007038751',
    #  u'list_date': u'2012-06-26'}
    url = str(endpoints.instruments()) + str(uuid) + '/'
    try:
        req = requests.get(url, timeout=15)
        req.raise_for_status()
        data = req.json()
    except requests.exceptions.HTTPError:
        raise RH_exception.InvalidInstrumentId()

    return data


class RobinhoodClient(Robinhood):
    def get_one_order(self, ibpyOrderId):
        rbOrder = self.order_history(ibpyOrderId)
        security = requests.get(rbOrder['instrument'], timeout=15).json()
        rbOrder['symbol'] = security['symbol']
        return rbOrder

    def get_all_orders(self):
        # (u'updated_at', u'2019-05-31T22:00:02.305547Z')
        # (u'ref_id', u'F4E69363-8CEA-42F3-8D24-D2532F0B7DD4')
        # (u'time_in_force', u'gfd')
        # (u'last_trail_price', None)
        # (u'fees', u'0.00')
        # (u'cancel', None)
        # (u'response_category', u'end_of_day')
        # (u'id', u'6e9975a3-48ee-4bd0-a5ab-df790668c905')
        # (u'cumulative_quantity', u'0.00000')
        # (u'stop_price', None)
        # (u'reject_reason', None)
        # (u'instrument', u'https://api.robinhood.com/instruments/3bd6f6b5-40a1-418b-97ed-2a40f509c738/')
        # (u'state', u'cancelled')
        # (u'trigger', u'immediate')
        # (u'override_dtbp_checks', False)
        # (u'last_trail_price_updated_at', None)
        # (u'type', u'limit')
        # (u'last_transaction_at', u'2019-05-31T22:00:01.303000Z')
        # (u'price', u'131.55000000')
        # (u'executions', [])              !!!! If status is Filled, executions is not empty   !!!
        # (u'executions', [{u'timestamp': u'2019-06-05T19:26:04.303000Z',
        #                   u'price': u'169.06000000',
        #                   u'quantity': u'2.00000',
        #                   u'id': u'64265d94-ac82-4951-b52a-0bbba9478ad1',
        #                   u'settlement_date': u'2019-06-07'},
        #                  {u'timestamp': u'2019-06-05T19:31:05.727000Z',
        #                   u'price': u'169.06000000',
        #                   u'quantity': u'56.00000',
        #                   u'id': u'3a19a253-4505-4247-9fce-091a10ff9062',
        #                   u'settlement_date': u'2019-06-07'},
        #                  {u'timestamp': u'2019-06-05T19:31:05.727000Z',
        #                   u'price': u'169.06000000',
        #                   u'quantity': u'2.00000',
        #                   u'id': u'9e898477-a395-470e-9bb8-3123229d0129',
        #                   u'settlement_date': u'2019-06-07'}])
        # (u'extended_hours', True)
        # (u'account', u'https://api.robinhood.com/accounts/5XC53467/')
        # (u'stop_triggered_at', None)
        # (u'url', u'https://api.robinhood.com/orders/6e9975a3-48ee-4bd0-a5ab-df790668c905/')
        # (u'created_at', u'2019-05-31T19:38:02.455345Z')
        # (u'override_day_trade_checks', False)
        # (u'average_price', None)
        # (u'position', u'https://api.robinhood.com/accounts/5XC53467/positions/3bd6f6b5-40a1-418b-97ed-2a40f509c738/')
        # (u'side', u'buy')
        # (u'quantity', u'180.00000')
        ans = []
        data = self.session.get(endpoints.orders(None), timeout=15).json()
        try:
            ans += data['results']
        except KeyError:
            print(__name__ + '::get_all_positions: data=%s' % (data,))

        while data['next']:
            data = requests.get(data['next'], timeout=15).json()
            if data['results']:
                ans += data['results']
        for anOrder in ans:
            security = requests.get(anOrder['instrument'], timeout=15).json()
            anOrder['symbol'] = security['symbol']
        return ans

    def get_all_positions(self):
        # u'shares_held_for_stock_grants': u'0.0000',
        # u'account': u'https://api.robinhood.com/accounts/5XC53467/',
        # u'pending_average_buy_price': u'169.0600',
        # u'shares_held_for_options_events': u'0.0000',
        # u'intraday_average_buy_price': u'0.0000',
        # u'url': u'https://api.robinhood.com/positions/5XC53467/10852882-d27f-4a20-8c77-002d7a09031f/',
        # u'shares_held_for_options_collateral': u'0.0000',
        # u'created_at': u'2018-11-30T20:13:29.592399Z',
        # u'updated_at': u'2019-06-05T19:31:06.203865Z',
        # u'shares_held_for_buys': u'0.0000',
        # u'average_buy_price': u'169.0600',
        # u'instrument': u'https://api.robinhood.com/instruments/10852882-d27f-4a20-8c77-002d7a09031f/',
        # u'intraday_quantity': u'0.0000',
        # u'shares_held_for_sells': u'0.0000',
        # u'shares_pending_from_options_events': u'0.0000',
        # u'quantity': u'60.0000'
        ans = []
        data = self.session.get(endpoints.positions() + '?nonzero=true', timeout=15).json()
        try:
            ans += data['results']
        except KeyError:
            print(__name__ + '::get_all_positions: data=%s' % (data,))

        while data['next']:
            data = self.session.get(data['next'], timeout=15).json()
            ans += data['results']
        for pos in ans:
            security = requests.get(pos['instrument'], timeout=15).json()
            pos['symbol'] = security['symbol']
        return ans
