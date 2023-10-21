# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""
from IBridgePy.constants import BrokerServiceName, LogLevel


# put here to avoid cyclic import
def _invoke_log(userConfig, caller, message):
    if userConfig.projectConfig.logLevel in [LogLevel.DEBUG, LogLevel.NOTSET]:
        print(__name__ + '::%s:%s' % (caller, message))


def get_brokerService(userConfig):
    name = userConfig.projectConfig.brokerServiceName
    t = None
    if name == BrokerServiceName.LOCAL_BROKER:
        from .BrokerService_Local import LocalBroker
        t = LocalBroker(userConfig,
                        userConfig.log,
                        userConfig.timeGenerator,
                        userConfig.singleTrader,
                        userConfig.dataFromServer,
                        userConfig.balanceLog)
    elif name == BrokerServiceName.IB:
        from .BrokerService_IB import InteractiveBrokers
        t = InteractiveBrokers(userConfig,
                               userConfig.log,
                               userConfig.timeGenerator,
                               userConfig.singleTrader,
                               userConfig.dataFromServer)
    elif name == BrokerServiceName.IBinsync:
        from .BrokerService_IB_insync import IBinsync
        t = IBinsync(userConfig,
                     userConfig.log,
                     userConfig.timeGenerator,
                     userConfig.singleTrader,
                     userConfig.dataFromServer)
    elif name == BrokerServiceName.ROBINHOOD:
        from .BrokerService_Robinhood import Robinhood
        t = Robinhood(userConfig,
                      userConfig.log,
                      userConfig.timeGenerator,
                      userConfig.singleTrader,
                      userConfig.dataFromServer)
    elif name == BrokerServiceName.TD:
        from .BrokerService_TdAmeritrade import TDAmeritrade
        t = TDAmeritrade(userConfig,
                         userConfig.log,
                         userConfig.timeGenerator,
                         userConfig.singleTrader,
                         userConfig.dataFromServer)
    else:
        print(__name__ + '::get_brokerService: cannot handle brokerServiceName=%s' % (name,))
    assert(t is not None)
    _invoke_log(userConfig, 'get_brokerService', 'created brokerService=%s' % (t,))
    return t
