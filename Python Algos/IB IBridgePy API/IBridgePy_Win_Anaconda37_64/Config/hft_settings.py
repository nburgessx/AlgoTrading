from IBridgePy.constants import TraderRunMode, DataProviderName, BrokerServiceName, BrokerClientName, BrokerName

MARKET_MANAGER = {
    'baseFreqOfProcessMessage': 0.25,  # second
}


REPEATER = {
    'slowdownInSecond': 0.25  # second
}

TRADER = {
    'runMode': TraderRunMode.HFT  # run handle_data by repBarFreq
}

PROJECT = {
    'dataProviderName': DataProviderName.IB,
    'brokerServiceName': BrokerServiceName.IB,
    'brokerClientName': BrokerClientName.IB,
    'brokerName': BrokerName.IB,
    'repBarFreq': 0.25,
}