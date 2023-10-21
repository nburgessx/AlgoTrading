# coding=utf-8
from models.AccountInfo import AccountInfo
from models.Order import KeyedIbridgePyOrders
from models.Position import KeyedPositionRecords
from copy import copy
from sys import exit


def stripe_exchange_primaryExchange_from_security(security):
    copy_security = copy(security)
    copy_security.exchange = ''
    copy_security.primaryExchange = ''
    return copy_security


'''
SingleTrader
    |- Broker (Key=str_brokerName; value=this::Broker
        |- Account (Key= str_accountCode; value=this::Account
            |- KeyPositionRecords (All positions, key=str_security_without_primaryExchange_exchange value=models::Position::PositionRecord)
            |- KeyedIbridgePyOrders (All ibridgepyOrders, key=orderId value=models::Order::IbridgePyOrder)
            |- AccountInfo (account Info, models::AccountInfo::AccountInfo)
'''


class SingleTrader(object):
    """
    The interface for outside world to use
    """

    def __init__(self, log):
        self._brokerNameDict = {}
        self._log = log
        self._accountCodeDict = None
        self._account_codes_with_real_value_from_broker = set()

    def __str__(self):
        ans = 'SingleTrader id=%s\n' % (id(self),)
        if not self._brokerNameDict:
            ans = ans[:-1] + '{Empty self._brokerNameDict}'
        for brokerName in self._brokerNameDict:
            ans += str(self._brokerNameDict[brokerName]) + '\n'
        return ans[:-1]

    def _find_account_by_brokerName_and_accountCode(self, brokerName, accountCode):
        self._log.notset(__name__ + '::_find_account_by_brokerName_and_accountCode: brokerName=%s accountCode=%s' % (brokerName, accountCode))
        if not isinstance(accountCode, str):
            self._log.error(__name__ + '::_find_account_by_brokerName_and_accountCode: EXIT, cannot handle accountCode=%s' % (accountCode,))
            exit()
        if brokerName not in self._brokerNameDict:
            self._brokerNameDict[brokerName] = Broker(brokerName, (accountCode,), self._log)
        self._accountCodeDict = self._brokerNameDict[brokerName].getAccountCodeDict()
        # self._log.info(__name__ + '::_find_account_by_brokerName_and_accountCode: tuple_accountCodes=%s self.accountCodeDict=%s' % (accountCode, self._accountCodeDict))
        if accountCode not in self._accountCodeDict:
            self._accountCodeDict[accountCode] = Account(accountCode, self._log)
        return self._accountCodeDict[accountCode]

    def set_from_send_req_to_server(self, brokerName, accountCode, ibpyOrderId):
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        account.keyedIbridgePyOrders.createFromPlaceOrder(ibpyOrderId)

    def set_position(self, brokerName, accountCode, positionRecord):
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        account.keyedPositionRecords.update(positionRecord)

    def set_orderStatus(self, brokerName, accountCode, orderStatusRecord):
        self._log.debug(__name__ + '::set_orderStatus: _brokerName=%s accountCode=%s orderStatusRecord=%s' % (
            brokerName, accountCode, orderStatusRecord))
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        account.keyedIbridgePyOrders.updateFromOrderStatus(orderStatusRecord)

    def set_openOrder(self, brokerName, accountCode, openOrderRecord):
        self._log.notset(__name__ + '::set_openOrder: _brokerName=%s accountCode=%s openOrderRecord=%s' % (
            brokerName, accountCode, openOrderRecord))
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        account.keyedIbridgePyOrders.updateFromOpenOrder(openOrderRecord)

    def set_accountSummary(self, brokerName, accountCode, accountSummaryRecord):
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        account.getAccountInfo().update_from_accountSummary(accountSummaryRecord)
        self._account_codes_with_real_value_from_broker.add(accountCode)

    def set_updateAccountValue(self, brokerName, accountCode, updateAccountValueRecord):
        self._log.notset(__name__ + '::set_updateAccountValue: brokerName=%s accountCode=%s updateAccountValueRecord=%s' % (brokerName, accountCode, updateAccountValueRecord))
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        account.getAccountInfo().update_from_updateAccountValue(updateAccountValueRecord)
        self._account_codes_with_real_value_from_broker.add(accountCode)

    def set_execDetails(self, brokerName, accountCode, execDetailsRecord):
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        account.keyedIbridgePyOrders.updateFromExecDetails(execDetailsRecord)

    def get_position(self, brokerName, accountCode, security):
        self._log.notset(
            __name__ + '::get_position: _brokerName=%s accountCode=%s security=%s' % (brokerName, accountCode, security))
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        adj_security = stripe_exchange_primaryExchange_from_security(security)
        return account.keyedPositionRecords.getPositionRecord(adj_security)

    def hold_any_position(self, brokerName, accountCode):
        """

        :param brokerName:
        :param accountCode:
        :return: bool
        """
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        return account.keyedPositionRecords.hold_any_position()

    def delete_every_position(self, brokerName, accountCode):
        """
        To run algo continuously, the positions must be always fresh. If a position is sell off, it will still stay in
        keyedPositionRecords forever. Then, iterating all keys will cause issues. The solution is to delete all positions
        before get_all_positions so that the positions are always fresh.
        """
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        account.keyedPositionRecords.delete_every_position()

    def get_all_positions(self, brokerName, accountCode):
        """
        :return: dictionary, keyed by str_security, value = PositionRecord
        """
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        return account.keyedPositionRecords.get_all_positions()

    def find_order(self, brokerName, accountCode, str_ibpyOrderId):
        """

        :param brokerName:
        :param accountCode:
        :param str_ibpyOrderId:
        :return: None if not find
        """

        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        if account.has_ibpyOrderId(str_ibpyOrderId):
            return account.get_ibridgePyOrder(str_ibpyOrderId)
        else:
            self._log.debug(__name__ + '::SingleTrader::find_order: account=%s does not have an OPEN order ibpyOrderId=%s. Maybe it is executed already.' % (accountCode, str_ibpyOrderId))
            return None

    def delete_every_order(self, brokerName, accountCode):
        """
        Web api bases brokers may not have all order info. For example, TD only keeps the orders for the latest 7 days.
        And get_all_order from broker will only return recent orders.
        It means that orders' latest status may not be updated if the order was placed a few days ago.
        The solution is to delete every order and request latest order info from broker.
        :param brokerName:
        :param accountCode:
        :return: None
        """
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        account.keyedIbridgePyOrders.delete_every_order()

    def get_all_orders(self, brokerName, accountCode):
        """

        :param brokerName:
        :param accountCode:
        :return: list of models::Order::IbridgePyOrder
        """
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        orderIdList = account.keyedIbridgePyOrders.get_all_ibpyOrderId()
        if len(orderIdList) == 0:
            return []
        ans = {}
        # print(__name__ + '::get_all_orders: orderIdList=%s' % (orderIdList,))
        for orderId in orderIdList:
            ans[orderId] = self.find_order(brokerName, accountCode, orderId)
        return ans

    def get_account_info(self, brokerName, accountCode, tag, meta='value'):
        # print(__name__ + '::get_account_info: id of singleTrader instance=%s' % (id(self), ))
        account = self._find_account_by_brokerName_and_accountCode(brokerName, accountCode)
        if meta == 'value':
            return account.getAccountInfo().get_value(tag)
        else:
            self._log.error(__name__ + '::get_account_info: EXIT meta=%s' % (meta,))
            raise NotImplementedError()

    def get_accountCode_by_ibpyOrderId(self, str_brokerName, str_ibpyOrderId):
        """
        This is a search logic, Exit if cannot find an accountCode
        :param str_brokerName:
        :param str_ibpyOrderId:
        :return:
        """
        self._log.notset(__name__ + '::get_accountCode_by_ibpyOrderId: str_brokerName=%s ibpyOrderId=%s' % (str_brokerName, str_ibpyOrderId))
        if str_brokerName in self._brokerNameDict:
            self._accountCodeDict = self._brokerNameDict[str_brokerName].getAccountCodeDict()
        else:
            print(__name__ + '::SingleTrader::get_accountCode_by_ibpyOrderId: EXIT, %s' % (self._brokerNameDict.keys(),))
            exit()
        for accountCode in self._accountCodeDict:
            ibridgePyOrder = self.find_order(str_brokerName, accountCode, str_ibpyOrderId)
            if ibridgePyOrder is not None:
                return accountCode

        # Cannot find any matched accountCode, Must exit
        self._log.error(__name__ + '::get_accountCode_by_ibpyOrderId: Cannot find accountCode by ibpyOrderId=%s' % (str_ibpyOrderId,))
        if len(self._accountCodeDict) == 1:
            return list(self._accountCodeDict.keys())[0]
        for acctCode in self._accountCodeDict:
            self._log.error('Possible accountCode=%s' % (acctCode,))
        exit()

    def get_all_active_accountCodes(self, brokerName):
        # self._accountCodeDict = self._brokerNameDict[brokerName].getAccountCodeDict()
        # return list(self._accountCodeDict.keys())
        return self._account_codes_with_real_value_from_broker


class Broker(object):
    def __init__(self, brokerName, tuple_accountCodes, log):
        self._log = log
        self._brokerName = brokerName
        self._accountCodeDict = {}
        for accountC in tuple_accountCodes:
            self._accountCodeDict[accountC] = Account(tuple_accountCodes, self._log)

    def __str__(self):
        ans = 'Broker=%s id=%s\n' % (self._brokerName, id(self))
        if not self._accountCodeDict:
            ans = ans[:-1] + '{Empty self._accountCodeDict}'
        for accountCode in self._accountCodeDict:
            ans += '%s\n' % (self._accountCodeDict[accountCode])
        return ans[:-1]

    def getAccountCodeDict(self):
        return self._accountCodeDict


class Account(object):
    def __init__(self, accountCode, log):
        self.accountCode = accountCode
        self._log = log
        self.keyedPositionRecords = KeyedPositionRecords(self._log)
        self.keyedIbridgePyOrders = KeyedIbridgePyOrders(accountCode, self._log)
        self._accountInfo = AccountInfo(self._log)

    def __str__(self):
        ans = 'Print models::Account=%s id=%s\n' % (self.accountCode, id(self))
        for item in [self.keyedPositionRecords, self.keyedIbridgePyOrders, self._accountInfo]:
            ans += '%s\n' % (item,)
        return ans[:-1]

    def getAccountInfo(self):
        return self._accountInfo

    def has_ibpyOrderId(self, ibpyOrderId):
        return self.keyedIbridgePyOrders.has_ibpyOrderId(ibpyOrderId)

    def get_ibridgePyOrder(self, ibpyOrderId):
        return self.keyedIbridgePyOrders.get_ibridgePyOrder(ibpyOrderId)
