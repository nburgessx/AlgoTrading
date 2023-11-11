# coding=utf-8
from IBridgePy.constants import LiveBacktest, BrokerServiceName, TimeGeneratorType, TraderRunMode, BrokerClientName, \
    BrokerName

PROJECT = {
    'liveOrBacktest': LiveBacktest.BACKTEST,
    'brokerServiceName': BrokerServiceName.LOCAL_BROKER,
    'brokerClientName': BrokerClientName.LOCAL,
    'brokerName': BrokerName.LOCAL
}

REPEATER = {
    'slowdownInSecond': 0.0
}

TIME_GENERATOR = {
    'timeGeneratorType': TimeGeneratorType.AUTO,  # Live, Auto, Custom
    'freq': '1T'  # 1S = 1 second; 1T = 1 minute; 1H = 1 hour; 1D = 1 day
}

TRADER = {
    'runMode': TraderRunMode.RUN_LIKE_QUANTOPIAN  # run handle_data every second, not run_like_quantopian
}
