# coding=utf-8
from BasicPyLib.Printable import PrintableII
from models.utils import print_IBCpp_contract, print_IBCpp_order
from IBridgePy.constants import OrderStatus
from sys import exit

"""
IB has three native callbacks related to order executions: OrderStatus, OpenOrder, ExecutionDetails
In IBridgePy, IbridgePyOrder is the basic entity to record order related info, keyed by orderId.
These three are spot time information, so that IbridgePyOrder only store the latest callbacks from IB server.

KeyedIbridegPyOrders (Interface for outside)
    |
    |--IbridgePyOrder (Key=orderId; value=models::Order::IbridgePyOrder)
        |
        |- OrderStatusRecord
        |- OpenOrderRecord
        |- ExecDetailsRecord
"""


class OrderStatusRecord(PrintableII):
    """
    This class is to match the callback of orderStatus
    """
    def __init__(self, ibpyOrderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,
                 whyHeld):
        if not isinstance(ibpyOrderId, str):
            print(__name__ + '::OrderStatusRecord::__init__: EXIT, ibpyOrderId must be an integer')
            exit()
        self._ibpyOrderId = ibpyOrderId
        self.status = status
        self.filled = filled
        self.remaining = remaining
        self.avgFillPrice = avgFillPrice
        self.permId = permId
        self.parentId = parentId
        self.lastFillPrice = lastFillPrice
        self.clientId = clientId
        self.whyHeld = whyHeld

    def getIbpyOrderId(self):
        return self._ibpyOrderId


class OpenOrderRecord(PrintableII):
    """
    This class is to match the callback of openOrder
    """
    def __init__(self, ibpyOrderId, contract, order, orderState):
        """
        Called back from IB server
        :param ibpyOrderId: string
        :param contract: IBCpp::Contract
        :param order:  IBCpp::Order
        :param orderState: IBCpp::OrderStatus
        """
        if not isinstance(ibpyOrderId, str):
            print(__name__ + '::OpenOrderRecord::__init__: EXIT, ibpyOrderId must be an integer')
            exit()

        self._ibpyOrderId = ibpyOrderId
        self.contract = contract
        self.order = order
        self.orderState = orderState

    def getIbpyOrderId(self):
        return self._ibpyOrderId


class ExecDetailsRecord(PrintableII):
    """
    This class is to match the callback of execDetails
    """
    def __init__(self, ibpyOrderId, contract, execution):
        if not isinstance(ibpyOrderId, str):
            print(__name__ + '::ExecDetailsRecord::__init__: EXIT, ibpyOrderId must be an integer')
            exit()

        self._ibpyOrderId = ibpyOrderId
        self.contract = contract
        self.execution = execution

    def getIbpyOrderId(self):
        return self._ibpyOrderId


class KeyedIbridgePyOrders(object):
    def __init__(self, accountCode, log):
        self.keyedIbridgePyOrders = {}  # keyed by orderId, value = this::IbridgePyOrder
        self.accountCode = accountCode
        self._log = log

    def __str__(self):
        if len(self.keyedIbridgePyOrders) == 0:
            return 'Empty KeyedIbridgePyOrders'
        ans = 'models::Order::KeyedIbridgePyOrders\n'
        for ibpyOrderId in self.keyedIbridgePyOrders:
            ans += '%s:%s\n' % (ibpyOrderId, self.keyedIbridgePyOrders[ibpyOrderId])
        return ans

    def createFromPlaceOrder(self, ibpyOrderId):
        if ibpyOrderId not in self.keyedIbridgePyOrders:
            self.keyedIbridgePyOrders[ibpyOrderId] = IbridgePyOrder(ibpyOrderId)
        else:
            pass
            # self._log.error(__name__ + '::KeyedIbridgePyOrders::createFromPlaceOrder: EXIT, ibpyOrderId=%s exist' % (ibpyOrderId,))
            # exit()

    def updateFromOpenOrder(self, openOrderRecord):
        self._log.notset(__name__ + '::KeyedIbridgePyOrders::updateFromOpenOrder: openOrderRecord=%s' % (openOrderRecord,))
        ibpyOrderId = openOrderRecord.getIbpyOrderId()
        if ibpyOrderId not in self.keyedIbridgePyOrders:
            self.keyedIbridgePyOrders[ibpyOrderId] = IbridgePyOrder(ibpyOrderId)
        self.keyedIbridgePyOrders[ibpyOrderId].openOrderRecord = openOrderRecord

    def updateFromOrderStatus(self, orderStatusRecord):
        ibpyOrderId = orderStatusRecord.getIbpyOrderId()
        if ibpyOrderId not in self.keyedIbridgePyOrders:
            self.keyedIbridgePyOrders[ibpyOrderId] = IbridgePyOrder(ibpyOrderId)
        self.keyedIbridgePyOrders[ibpyOrderId].orderStatusRecord = orderStatusRecord
        # print(__name__ + '::updateFromOrderStatus', self.keyedIbridgePyOrders[ibpyOrderId])

    def updateFromExecDetails(self, execDetailsRecord):
        ibpyOrderId = execDetailsRecord.getIbpyOrderId()
        if ibpyOrderId not in self.keyedIbridgePyOrders:
            self.keyedIbridgePyOrders[ibpyOrderId] = IbridgePyOrder(ibpyOrderId)
        self.keyedIbridgePyOrders[ibpyOrderId].execDetailsRecord = execDetailsRecord

    def has_ibpyOrderId(self, ibpyOrderId):
        return ibpyOrderId in self.keyedIbridgePyOrders

    def get_ibridgePyOrder(self, ibpyOrderId):
        """
        Get ibridgePyOrder, Must return one, Otherwise exit
        :param ibpyOrderId:
        :return: models::Order::IbridgePyOrder
        """
        if self.has_ibpyOrderId(ibpyOrderId):
            return self.keyedIbridgePyOrders[ibpyOrderId]
        else:
            self._log.error(__name__ + '::get_ibridgePyOrder: EXIT, cannot get order. accountCode=%s ibpyOrderId=%s' % (self.accountCode, ibpyOrderId))
            exit()

    def get_all_ibpyOrderId(self):
        return list(self.keyedIbridgePyOrders.keys())  # Python 2 and 3 compatibility

    def delete_every_order(self):
        self.keyedIbridgePyOrders = {}


class IbridgePyOrder(object):
    def __init__(self, ibpyOrderId=None, requestedContract=None, requestedOrder=None, createdTime=None):
        if ibpyOrderId is not None and not isinstance(ibpyOrderId, str):
            print(__name__ + '::IbridgePyOrder::__init__: EXIT, ibpyOrderId must be a string')
            exit()
        self._ibpyOrderId = ibpyOrderId
        self.openOrderRecord = None
        self.orderStatusRecord = None
        self.execDetailsRecord = None
        self.requestedContract = requestedContract
        self.requestedOrder = requestedOrder
        self.created = createdTime  # Quantopian, the time when this order is created by IBridgePy this session

    def __str__(self):
        if self.requestedOrder is not None:  # IBridgePy created orders
            ans = '{ibpyOrderId=%s status=%s order=%s contract=%s}' % (
                self._ibpyOrderId, self.status, print_IBCpp_order(self.requestedOrder),
                print_IBCpp_contract(self.requestedContract))
        else:  # orders are called-back from IB server
            if self.openOrderRecord is None:
                ans = '{ibpyOrderId=%s status=%s order=%s contract=%s}' % (self.getIbpyOrderId(), self.status, 'NONE', 'NONE')
            else:
                if self.get_value_by_tag('whyHeld') == '':
                    if self.openOrderRecord.order['orderId'] not in [0, -1]:
                        ans = '{ibpyOrderId=%s status=%s order=%s contract=%s}' % (
                            self.getIbpyOrderId(), self.status, print_IBCpp_order(self.openOrderRecord.order),
                            print_IBCpp_contract(self.openOrderRecord.contract))
                    else:
                        ans = '{permId=%s status=%s order=%s contract=%s}' % (
                            self.getIbpyOrderId(), self.status, print_IBCpp_order(self.openOrderRecord.order),
                            print_IBCpp_contract(self.openOrderRecord.contract))
                else:
                    if self.openOrderRecord.order['orderId'] not in [0, -1]:
                        ans = '{ibpyOrderId=%s status=%s order=%s contract=%s whyHeld=%s}' % (
                            self.getIbpyOrderId(), self.status, print_IBCpp_order(self.openOrderRecord.order),
                            print_IBCpp_contract(self.openOrderRecord.contract), self.get_value_by_tag('whyHeld'))
                    else:
                        ans = '{permId=%s status=%s order=%s contract=%s  whyHeld=%s}' % (
                            self.getIbpyOrderId(), self.status, print_IBCpp_order(self.openOrderRecord.order),
                            print_IBCpp_contract(self.openOrderRecord.contract), self.get_value_by_tag('whyHeld'))

        return ans

    @property
    def orderId(self):
        return self._ibpyOrderId

    @property
    def status(self):  # IbridgePyOrder
        if self.orderStatusRecord is not None:
            return self.orderStatusRecord.status
        else:
            return OrderStatus.PRESUBMITTED

    @property
    def amount(self):  # Quantopian, number of shares
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order['totalQuantity']
        else:
            return self.requestedOrder['totalQuantity']

    @property
    def filled(self):  # Quantopian, shares that have been filled.
        if self.orderStatusRecord is not None:
            return self.orderStatusRecord.filled
        else:
            return None

    @property
    def remaining(self):  # IbridgePyOrder
        if self.orderStatusRecord is not None:
            return self.orderStatusRecord.remaining
        else:
            return None

    @property
    def avgFillPrice(self):  # IbridgePyOrder
        if self.orderStatusRecord is not None:
            return self.orderStatusRecord.avgFillPrice
        else:
            return None

    @property
    def lastFillPrice(self):
        return self.get_value_by_tag('lastFillPrice')

    @property
    def action(self):  # IbridgePyOrder
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order.get('action', None)
        else:
            return None

    def getIbOrderId(self):
        """
        get IBCpp::Order().orderId
        :return: int
        """
        if self.openOrderRecord:
            return self.openOrderRecord.order.get('orderId', None)
        else:
            return self.requestedOrder['orderId']

    def getIbpyOrderId(self):
        """
        get IBridgePy order id
        :return: string
        """
        return self._ibpyOrderId

    def get_value_by_tag(self, tag):
        """
        Convenient function for IBridgePy internal
        :param tag: str, name of the field
        :return: value of the field of the given tag
        """
        if hasattr(self, tag):
            return getattr(self, tag)
        else:
            if tag in ['status', 'filled', 'remaining', 'avgFillPrice', 'permId', 'parentId',
                       'lastFillPrice', 'clientId', 'whyHeld']:
                if self.orderStatusRecord:
                    return getattr(self.orderStatusRecord, tag)
                else:
                    print(__name__ + '::get_value_by_tag: missing orderStatusRecord tag=%s return empty string to mitigate the issue that comes from IB server.' % (tag,))
                    return ''
            elif tag in ['execution']:
                return getattr(self.execDetailsRecord, tag)
            elif tag in ['orderType', 'orderRef', 'tif', 'ocaGroup', 'ocaType', 'account']:  # account = accountCode
                if self.openOrderRecord:
                    # print(type(self.openOrderRecord.order), self.openOrderRecord.order)
                    return self.openOrderRecord.order.get(tag, None)
                else:
                    return getattr(self.requestedOrder, tag)
            elif tag in ['symbol', 'secType', 'exchange', 'primaryExchange', 'expiry', 'multiplier', 'right', 'strike',
                         'localSymbol']:
                return getattr(self.openOrderRecord.contract, tag)
            elif tag == 'IbridgePyOrder':
                return self
            else:
                print(__name__ + '::IbridgePyOrder::get_value: EXIT, cannot find tag=%s' % (tag,))
                exit()

    @property
    def sid(self):  # Quantopian
        raise None

    @property
    def limit_reached(self):  # Quantopian, return bool
        raise NotImplementedError

    @property
    def stop_reached(self):  # Quantopian, return bool
        raise NotImplementedError

    @property
    def filledTime(self):  # Quantopian, the time when this order is filled.
        if self.execDetailsRecord is not None:
            return self.execDetailsRecord.execution.time
        else:
            return None

    @property
    def stop(self):  # Quantopian, stop price
        if self.openOrderRecord is not None:
            # print(f"{__name__}::stop: self.openOrderRecord={self.openOrderRecord} type(self.openOrderRecord)={type(self.openOrderRecord)}")
            return self.openOrderRecord.order.get('auxPrice', None)
        else:
            return None

    @property
    def limit(self):  # Quantopian, limit price
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order['lmtPrice']
        else:
            return self.requestedOrder['lmtPrice']

    @property
    def commission(self):  # Quantopian, commission
        if self.openOrderRecord is not None:
            return self.openOrderRecord.orderState.commission
        else:
            return None

    @property
    def contract(self):
        if self.openOrderRecord is not None:
            return self.openOrderRecord.contract
        else:
            return self.requestedContract

    @property
    def order(self):  # IbridgePyOrder
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order
        else:
            return self.requestedOrder

    @property
    def orderState(self):  # IbridgePyOrder
        if self.openOrderRecord is not None:
            return self.openOrderRecord.orderState
        else:
            return None

    @property
    def parentOrderId(self):  # IbridgePyOrder
        if self.openOrderRecord is not None:
            return self.openOrderRecord.order.get('parentId', None)
        else:
            return None
