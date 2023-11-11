from BasicPyLib.Printable import PrintableII

"""
There are two native IB callbacks: accountValue and accountSummary
accountValue is for single account
accountSummary is for multiple accounts
In IBridgePy, AccountInfo is the interface for outside
AccountInfo
    - AccountValues
        Keyed by AccountValueRecord.key, Value = AccountValueRecord 
    - AccountSummaries
        Keyed by AccountSummaryRecord.tag, Value = AccountValueRecord

"""


class UpdateAccountValueRecord(PrintableII):
    """
    Single account from IB uses AccountValues callback
    This class is to match the callback of updateAccountValue
    """
    def __init__(self, key, value, currency, accountCode):
        self.key = key
        self.value = value
        self.currency = currency
        self.accountCode = accountCode


class AccountSummaryRecord(PrintableII):
    """
    Multi accounts from IB uses AccountSummaries callback
    This class is to match the callback of accountSummary
    """
    def __init__(self, reqId, accountCode, tag, value, currency):
        self.reqId = reqId
        self.accountCode = accountCode
        self.tag = tag
        self.value = value
        self.currency = currency


class AccountValues:
    """
    This class is to organize updateAccountValue callbacks
    Keyed by AccountValueRecord.key, Value = AccountValueRecord
    """
    def __init__(self, log):
        self._updateAccountValueRecords = {}  # Keyed by AccountValueRecord.key, Value = AccountValueRecord
        self.log = log  # not used right now

    def __str__(self):
        if not self._updateAccountValueRecords:
            return 'EMPTY models::AccountInfo::AccountValue::_updateAccountValueRecords'
        else:
            ans = 'print models::AccountInfo::AccountValue::_updateAccountValueRecords\n'
            for key in self._updateAccountValueRecords:
                ans += '''%s:%s\n''' % (key, self._updateAccountValueRecords[key])
            return ans

    def update(self, accountValueRecord):
        self._updateAccountValueRecords[accountValueRecord.key] = accountValueRecord

    def getValue(self, key):
        if key in self._updateAccountValueRecords:
            return self._updateAccountValueRecords[key].value
        else:
            return None

    def getCurrency(self, key):
        if key in self._updateAccountValueRecords:
            return self._updateAccountValueRecords[key].currency
        else:
            return None


class AccountSummaries:
    """
    This class is to organize accountSummary callbacks
    keyed by AccountSummaryRecord.tag, Value = AccountSummaryRecord
    """
    def __init__(self, log):
        self._accountSummaryRecords = {}  # keyed by AccountSummaryRecord.tag, Value = AccountSummaryRecord
        self.log = log  # Not used right now

    def __str__(self):
        if not self._accountSummaryRecords:
            return 'EMPTY models::AccountInfo::AccountSummaries::_accountSummaryRecords'
        else:
            ans = '''print models::AccountInfo::AccountSummaries::_accountSummaryRecords\n'''
            for tag in self._accountSummaryRecords:
                ans += '''%s\n''' % (str(self._accountSummaryRecords[tag]),)
            return ans

    def update(self, accountSummaryRecord):
        tag = accountSummaryRecord.tag
        self._accountSummaryRecords[tag] = accountSummaryRecord

    def getValue(self, tag):
        if tag in self._accountSummaryRecords:
            return self._accountSummaryRecords[tag].value
        else:
            return None

    def getCurrency(self, tag):
        if tag in self._accountSummaryRecords:
            return self._accountSummaryRecords[tag].currency
        else:
            return None


class AccountInfo:
    def __init__(self, log):
        self.log = log
        self._accountValues = AccountValues(self.log)
        self._accountSummaries = AccountSummaries(self.log)

    def __str__(self):
        ans = 'Print models::AccountInfo::AccountInfo\n'
        for item in [self._accountValues, self._accountSummaries]:
            ans += '%s\n' % (item,)
        return ans

    def update_from_accountSummary(self, accountSummaryRecord):
        self._accountSummaries.update(accountSummaryRecord)

    def update_from_updateAccountValue(self, updateAccountValueRecord):
        self._accountValues.update(updateAccountValueRecord)

    def get_value(self, tag):
        ans = self._accountValues.getValue(tag)
        if ans is None:
            return self._accountSummaries.getValue(tag)
        return ans
