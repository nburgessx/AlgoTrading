# coding=utf-8
from IBridgePy.constants import BrokerServiceName, DataProviderName, BrokerClientName, BrokerName

PROJECT = {
    'dataProviderName': DataProviderName.IB,
    'brokerServiceName': BrokerServiceName.IB,
    'brokerClientName': BrokerClientName.IB,
    'brokerName': BrokerName.IB
}


BROKER_CLIENT = {
    'IB_CLIENT': {
        'accountCode': '',
        'port': 7496,
        'clientId': 9,
        'syncOrderId': False
    }
}
