# coding=utf-8
from decimal import Decimal

class PositionRecord(object):
    """
    This class is to match the callback of position
    """
    def __init__(self, str_security_no_exchange_no_primaryExchange, amount, cost_basis, contract):
        """
        !!!! str_security does not have primaryExchange and exchange !!!!
        positions are aggregations of a few position that may be traded at different exchange.
        """
        self.str_security = str_security_no_exchange_no_primaryExchange
        self.amount = amount
        self.cost_basis = cost_basis
        self.contract = contract  # the original contract is documented in case it is needed for some users

    def __str__(self):
        return '{security=%s amount=%s cost_basis=%s}' % (self.str_security, self.amount, self.cost_basis)

    @property
    def price(self):
        return self.cost_basis


class KeyedPositionRecords(object):
    """
    Only store positions when amount > 0
    Delete positions when amount == 0
    keyed by str_security_no_exchange_no_primaryExchange, value=this::PositionRecord

    """

    def __init__(self, log):
        self._keyedPositionRecords = {}  # keyed by str_security, value = PositionRecord
        self._log = log

    def __str__(self):
        if len(self._keyedPositionRecords) == 0:
            return 'Empty keyedPositionRecords'
        ans = 'Print KeyedPositionRecords\n'
        for key in self._keyedPositionRecords:
            ans += '%s:%s\n' % (key, self._keyedPositionRecords[key])
        return ans

    def update(self, positionRecord):
        # Only store positions when amount != 0
        # Delete positions when amount == 0
        if positionRecord.amount == 0:
            if positionRecord.str_security in self._keyedPositionRecords:
                del self._keyedPositionRecords[positionRecord.str_security]
        else:
            self._keyedPositionRecords[positionRecord.str_security] = positionRecord

    def getPositionRecord(self, security):
        # print(__name__ +'::getPositionRecord::security=%s' % (security.full_print(),))
        str_security = security.full_print()
        if str_security in self._keyedPositionRecords:
            return self._keyedPositionRecords[str_security]
        else:
            # print(__name__ +'::getPositionRecord')
            # print(list(self.keyedPositionRecords.keys()))
            return PositionRecord(str_security, Decimal(0), 0.0, None)

    def hold_any_position(self):
        return len(self._keyedPositionRecords) > 0

    def get_all_positions(self):
        """
        :return: dictionary, keyed by str_security, value = PositionRecord
        """
        return self._keyedPositionRecords

    def delete_every_position(self):
        self._keyedPositionRecords = {}
