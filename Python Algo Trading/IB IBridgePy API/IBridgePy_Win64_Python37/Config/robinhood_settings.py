# coding=utf-8
from IBridgePy.constants import BrokerServiceName, DataProviderName, BrokerClientName, BrokerName

PROJECT = {
    'dataProviderName': DataProviderName.ROBINHOOD,
    'brokerServiceName': BrokerServiceName.ROBINHOOD,
    'brokerClientName': BrokerClientName.ROBINHOOD,
    'brokerName': BrokerName.ROBINHOOD
}


MARKET_MANAGER = {
    'baseFreqOfProcessMessage': 0,  # dont run Trader::processMessage()
}
