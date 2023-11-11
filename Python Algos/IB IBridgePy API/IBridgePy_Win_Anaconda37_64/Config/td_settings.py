# coding=utf-8
from IBridgePy.constants import BrokerServiceName, DataProviderName, BrokerClientName, BrokerName

PROJECT = {
    'dataProviderName': DataProviderName.TD,
    'brokerServiceName': BrokerServiceName.TD,
    'brokerClientName': BrokerClientName.TD,
    'brokerName': BrokerName.TD
}


MARKET_MANAGER = {
    'baseFreqOfProcessMessage': 0,  # dont run Trader::processMessage()
}
