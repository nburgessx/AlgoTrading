import os
import sys

from ibapi.softdollartier import SoftDollarTier

sys.path.append(os.path.join(os.getcwd(), '..', 'source', 'pythonclient'))
import json
from decimal import Decimal
from ibapi.order import Order
from ibapi.contract import Contract
from ibapi.scanner import ScannerSubscription


def order_converter(json_order):
    py_order = json.loads(json_order)
    ans = Order()
    for key in py_order:
        if key != 'softDollarTier':
            setattr(ans, key, py_order[key])
    if 'softDollarTier' in py_order:
        ans.softDollarTier = softDollarTier_converter(py_order['softDollarTier'])
    ans.totalQuantity = Decimal(ans.totalQuantity)
    if ans.filledQuantity:
        ans.filledQuantity = Decimal(ans.filledQuantity)
    return ans


def softDollarTier_converter(a_dict):
    ans = SoftDollarTier()
    for key in ['name', 'val', 'displayName']:
        setattr(ans, key, a_dict[key])
    return ans


def contract_converter(json_order):
    py_order = json.loads(json_order)
    # print(f'{__name__}::contract_converter: type(py_order)={type(py_order)} py_order={py_order}')
    if isinstance(py_order, str):
        py_order = json.loads(py_order)
    ans = Contract()
    for key in py_order:
        setattr(ans, key, py_order[key])
    # print(ans)
    return ans


def scannerSubscription_converter(json_order):
    py_order = json.loads(json_order)
    ans = ScannerSubscription()
    for key in py_order:
        setattr(ans, key, py_order[key])
    # print(ans)
    return ans


if __name__ == '__main__':

    myorder = {
        'action': 'BUY',
        'orderType': 'MKT',
        'totalQuantity': 10,
    }
    order_converter(json.dumps(myorder))