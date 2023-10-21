# coding=utf-8
from sys import exit
from IBridgePy.IbridgepyTools import check_same_security


class Context(object):
    def __init__(self, parentTrader, accountCodeSet):
        self.parentTrader = parentTrader
        self.portfolioQ = {}
        self.accountCodeSet = accountCodeSet
        for acctCode in self.accountCodeSet:
            self.portfolioQ[acctCode] = Portfolio(parentTrader, acctCode)
        if len(self.accountCodeSet) == 1:
            self.accountCode = list(self.accountCodeSet)[0]
        else:
            self.accountCode = None

    @property
    def portfolio(self):
        return self.portfolioQ[self.accountCode]


class Positions(dict):
    """
    Learned from Quantopian
    When there is no position, it is an empty dict.
    When key is missing, it creates an instance.
    IBridgePy take advantage of __missing__ to process something like context.portfolio.positions[symbol('SPY')]
    """

    # noinspection PyMissingConstructor
    def __init__(self, parentTrader, accountCode):
        self.parentTrader = parentTrader
        self.accountCode = accountCode

    def __missing__(self, security):  # When key is missing, it creates an instance.
        return self.parentTrader.get_position(security, self.accountCode)

    def __len__(self):  # override len() of dict
        allPositions = self.parentTrader.get_all_positions(self.accountCode)
        return len(allPositions)

    def __str__(self):
        allPositions = self.parentTrader.get_all_positions(self.accountCode)
        return str(allPositions)

    def __iter__(self):  # override for loop
        for ct in self.keys():
            yield ct

    def __contains__(self, item):  # override in operator
        for security in self.keys():
            if check_same_security(item, security):
                return True
        return False

    def keys(self):
        allPositions = self.parentTrader.get_all_positions(self.accountCode)
        return list(allPositions.keys())

    def items(self):
        allPositions = self.parentTrader.get_all_positions(self.accountCode)
        return list(allPositions.items())


class Portfolio(object):
    def __init__(self, parentTrader, accountCode):
        self.parentTrader = parentTrader
        self.accountCode = accountCode
        self.starting_cash = 0  # sames as quantopian, It is a fixed value during IBridgePy session
        self.startDate = None
        self.positions = Positions(self.parentTrader, self.accountCode)

    @property
    def capital_used(self):  # sames as quantopian
        if self.starting_cash == 0:
            print(__name__ + '::Portfolio::returns: start_cash is not initialized, EXIT')
            exit()
        return self.starting_cash - self.cash

    @property
    def cash(self):  # sames as quantopian
        return self.parentTrader.getBrokerService().get_account_info(self.accountCode, 'TotalCashValue')

    @property
    def pnl(self):  # sames as quantopian
        return self.parentTrader.getBrokerService().get_account_info(self.accountCode, 'UnrealizedPnL')

    @property
    def portfolio_value(self):  # sames as quantopian
        return self.parentTrader.getBrokerService().get_account_info(self.accountCode, 'NetLiquidation')

    @property
    def positions_value(self):  # sames as quantopian
        return self.parentTrader.getBrokerService().get_account_info(self.accountCode, 'GrossPositionValue')

    @property
    def returns(self):  # sames as quantopian
        if self.starting_cash == 0:
            print(__name__ + '::Portfolio::returns: start_cash is not initialized, EXIT')
            exit()
        return (self.portfolio_value - self.starting_cash) / self.starting_cash

    @property
    def start_date(self):  # sames as quantopian
        if self.startDate is None:
            print(__name__ + '::Portfolio::start_date: start_date is not initialized, EXIT')
            exit()
        return self.startDate
