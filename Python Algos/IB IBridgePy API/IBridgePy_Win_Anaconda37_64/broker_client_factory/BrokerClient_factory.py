# -*- coding: utf-8 -*-
"""
All rights reserved.
@author: IBridgePy@gmail.com
"""
from IBridgePy.constants import BrokerClientName, LogLevel
from broker_client_factory.CustomErrors import CustomError
from models.Data import DataFromServer
from models.SingleTrader import SingleTrader


# put here to avoid cyclic import
def _invoke_log(userConfig, caller, message, should_print=False):
    if should_print or userConfig.projectConfig.logLevel in [LogLevel.DEBUG, LogLevel.NOTSET]:
        print(__name__ + '::%s:%s' % (caller, message))


def _build_IB_client(userConfig, searchPort, portList, newTrader, newDataFromServer, ibInsync=False):
    _invoke_log(userConfig, '_build_IB_client', f'start to build IB client', should_print=False)
    t = None
    if newTrader:
        trader = SingleTrader(userConfig.log)
    else:
        trader = userConfig.singleTrader
    if newDataFromServer:
        data = DataFromServer()
    else:
        data = userConfig.dataFromServer
    if searchPort:
        is_connection_successful = False
        for port in portList:
            for host in ['localhost', '127.0.0.1']:
                """
                !!! BrokerClient class does not have any constructor because it extends IBClient from IBCpp.
                !!! To create an instance, just create and then call setup_this_client
                !!! Every loop, has to create a new instance. Otherwise, the created instance will be labeled by IB as error 501 and cannot connect again.
                """
                if ibInsync:
                    from .BrokerClient_IBinsync import IBinsync
                    t = IBinsync()
                else:
                    from .BrokerClient_IB_regular import IBRegular
                    t = IBRegular()
                try:
                    t.setup_this_client(userConfig,
                                        userConfig.log,
                                        userConfig.projectConfig.accountCode,
                                        userConfig.projectConfig.rootFolderPath,
                                        trader,
                                        data,
                                        userConfig.timeGenerator,
                                        host,
                                        port,
                                        userConfig.brokerClientConfig.IB_CLIENT['clientId'],
                                        userConfig.brokerClientConfig.IB_CLIENT['syncOrderId'],
                                        userConfig.projectConfig.autoReconnectPremium)
                    t.connectWrapper()
                    userConfig.brokerClientConfig.IB_CLIENT['port'] = port
                    userConfig.brokerClientConfig.IB_CLIENT['host'] = host
                    userConfig.log.debug(f'port={port} is correct and set port to userConfig.brokerClientConfig.IB_CLIENT')
                    userConfig.log.debug(f'host={host} is correct and set host to userConfig.brokerClientConfig.IB_CLIENT')
                    userConfig.log.info('Connected to Interactive Brokers')
                    is_connection_successful = True
                    break
                except CustomError as e:
                    if e.error_code in [502, 501, 504]:
                        # errorCode=501 errorMessage=Already connected.
                        # errorCode:502 errorId:-1 errorMessage=Couldn't connect to TWS.  Confirm that "Enable ActiveX and Socket Clients" is enabled on the TWS "Configure->API" menu.
                        # errorCode=504 errorMessage=Not connected
                        pass
                    else:
                        raise e
                except RuntimeError as e:
                    if str(e) != 'Connection failed':
                        raise e
            if is_connection_successful:
                break
    else:  # Do not search port
        if ibInsync:
            from .BrokerClient_IBinsync import IBinsync
            t = IBinsync()
        else:
            from .BrokerClient_IB_regular import IBRegular
            t = IBRegular()
        t.setup_this_client(userConfig,
                            userConfig.log,
                            userConfig.projectConfig.accountCode,
                            userConfig.projectConfig.rootFolderPath,
                            trader,
                            data,
                            userConfig.timeGenerator,
                            userConfig.brokerClientConfig.IB_CLIENT['host'],
                            userConfig.brokerClientConfig.IB_CLIENT['port'],
                            userConfig.brokerClientConfig.IB_CLIENT['clientId'],
                            userConfig.brokerClientConfig.IB_CLIENT['syncOrderId'],
                            userConfig.projectConfig.autoReconnectPremium)
        t.connectWrapper()
    return t


class BrokerClientFactory(object):
    def __init__(self):
        self._brokerClientFactoryDict = {}

    def __str__(self):
        if not self._brokerClientFactoryDict:
            return '{Empty dict}'
        ans = '{'
        for key in self._brokerClientFactoryDict:
            ans += '%s:%s ' % (key, self._brokerClientFactoryDict[key])
        ans = ans[:-1] + '}'
        return ans

    def disconnect_all_client(self):
        for key in self._brokerClientFactoryDict:
            self._brokerClientFactoryDict[key].disconnectWrapper()

    def _find_brokerClient_in_cache(self, brokerClientName, userConfig):
        t = None
        if brokerClientName in self._brokerClientFactoryDict:
            t = self._brokerClientFactoryDict[brokerClientName]
            _invoke_log(userConfig, '_find_brokerClient_in_cache', f'found brokerClient={t} in brokerClientFactory', should_print=False)
            return t
        return t

    def _delete_brokerClient_in_cache(self, brokerClientName, userConfig):
        if brokerClientName in self._brokerClientFactoryDict:
            del self._brokerClientFactoryDict[brokerClientName]
            _invoke_log(userConfig, '_delete_brokerClient_in_cache', f'brokerClient={brokerClientName} is deleted in factory cache.')

    def get_brokerClient_by_name(self, brokerClientName, userConfig, check_cache=True):
        _invoke_log(userConfig, 'get_dataClient_by_name', brokerClientName, should_print=False)
        if check_cache:
            t = self._find_brokerClient_in_cache(brokerClientName, userConfig)
            if t:
                return t
        return self._create_brokerClient_by_name(brokerClientName, userConfig)

    def _create_brokerClient_by_name(self, brokerClientName, userConfig):
        _invoke_log(userConfig, '_create_brokerClient_by_name', brokerClientName, should_print=False)
        if brokerClientName == BrokerClientName.LOCAL:
            from .BrokerClient_Local import ClientLocalBroker
            t = ClientLocalBroker()
            accountCode = 'testAccountCode'
            t.setup_this_client(userConfig,
                                userConfig.log,
                                accountCode,
                                userConfig.projectConfig.rootFolderPath,
                                SingleTrader(userConfig.log),
                                DataFromServer(),
                                userConfig.timeGenerator,
                                None,
                                userConfig.transactionLog,
                                userConfig.backtesterConfig.simulateCommission)
            t.connectWrapper()
        elif brokerClientName == BrokerClientName.IB:
            t = _build_IB_client(userConfig, userConfig.projectConfig.autoSearchPortNumber, userConfig.projectConfig.searchPortList, True, True, ibInsync=False)
            t.connectWrapper()
        elif brokerClientName == BrokerClientName.IBinsync:
            t = _build_IB_client(userConfig, userConfig.projectConfig.autoSearchPortNumber, userConfig.projectConfig.searchPortList, True, True, ibInsync=True)

        elif brokerClientName == BrokerClientName.ROBINHOOD:
            from .BrokerClient_Robinhood import BrokerClientRobinhood
            from .Robinhood.robinhoodClient import RobinhoodClient

            robinhoodClient = RobinhoodClient()
            t = BrokerClientRobinhood()
            accountCode = userConfig.brokerClientConfig.ROBINHOOD_CLIENT['accountCode']
            if not accountCode:
                raise RuntimeError("ROBINHOOD_CLIENT['accountCode'] is empty. Please check setting.py --> BROKER_CLIENT --> ROBINHOOD_CLIENT --> accountCode")
            t.setup_this_client(userConfig,
                                userConfig.log,
                                userConfig.projectConfig.rootFolderPath,
                                SingleTrader(userConfig.log),
                                DataFromServer(),
                                userConfig.timeGenerator,
                                robinhoodClient,
                                accountCode,
                                userConfig.brokerClientConfig.ROBINHOOD_CLIENT['username'],
                                userConfig.brokerClientConfig.ROBINHOOD_CLIENT['password'])
            t.connectWrapper()
        elif brokerClientName == BrokerClientName.TD:
            from broker_client_factory.TdAmeritrade import TDClient
            from .BrokerClient_TdAmeritrade import BrokerClientTdAmeritrade
            tdClient = TDClient(userConfig.brokerClientConfig.TD_CLIENT['refreshToken'],
                                userConfig.brokerClientConfig.TD_CLIENT['apiKey'],
                                userConfig.brokerClientConfig.TD_CLIENT['refreshTokenCreatedOn'],
                                [userConfig.projectConfig.accountCode],
                                userConfig.log)
            t = BrokerClientTdAmeritrade()
            accountCode = userConfig.brokerClientConfig.TD_CLIENT['accountCode']
            if not accountCode:
                raise RuntimeError(
                    "TD_CLIENT['accountCode'] is empty. Please check setting.py --> BROKER_CLIENT --> TD_CLIENT --> accountCode")
            t.setup_this_client(userConfig,
                                userConfig.log,
                                userConfig.projectConfig.rootFolderPath,
                                SingleTrader(userConfig.log),
                                DataFromServer(),
                                userConfig.timeGenerator,
                                tdClient,
                                accountCode)
            t.connectWrapper()
        else:
            raise RuntimeError(__name__ + '::get_brokerClient: cannot handle brokerClientName = %s' % (brokerClientName,))
        _invoke_log(userConfig, 'get_brokerClient', 'created brokerClient=%s id=%s dataProvider=None is correct at the moment, setup_services will invoke later.' % (t.name, id(t)))
        if t.name == BrokerClientName.IBinsync:
            self._brokerClientFactoryDict[BrokerClientName.IB] = t
        self._brokerClientFactoryDict[t.name] = t
        return t

    def get_brokerClient_by_userConfig(self, userConfig, check_cache=True, delete_cache=False):
        _invoke_log(userConfig, 'get_brokerClient_by_userConfig', 'start', should_print=False)
        brokerClientName = userConfig.projectConfig.brokerClientName
        if check_cache:
            t = self._find_brokerClient_in_cache(brokerClientName, userConfig)
            if t:
                return t

        if delete_cache:
            self._delete_brokerClient_in_cache(brokerClientName, userConfig)

        if brokerClientName == BrokerClientName.LOCAL:
            from .BrokerClient_Local import ClientLocalBroker
            t = ClientLocalBroker()
            t.setup_this_client(userConfig,
                                userConfig.log,
                                userConfig.projectConfig.accountCode,
                                userConfig.projectConfig.rootFolderPath,
                                userConfig.singleTrader,
                                userConfig.dataFromServer,
                                userConfig.timeGenerator,
                                userConfig.dataProvider,
                                userConfig.transactionLog,
                                userConfig.backtesterConfig.simulateCommission)
            t.connectWrapper()
        elif brokerClientName == BrokerClientName.IB:
            t = _build_IB_client(userConfig, userConfig.projectConfig.autoSearchPortNumber, userConfig.projectConfig.searchPortList, False, False)

        elif brokerClientName == BrokerClientName.IBinsync:
            t = _build_IB_client(userConfig, userConfig.projectConfig.autoSearchPortNumber, userConfig.projectConfig.searchPortList, False, False, True)

        elif brokerClientName == BrokerClientName.ROBINHOOD:
            from .BrokerClient_Robinhood import BrokerClientRobinhood
            from .Robinhood.robinhoodClient import RobinhoodClient

            robinhoodClient = RobinhoodClient()
            t = BrokerClientRobinhood()
            t.setup_this_client(userConfig,
                                userConfig.log,
                                userConfig.projectConfig.rootFolderPath,
                                userConfig.singleTrader,
                                userConfig.dataFromServer,
                                userConfig.timeGenerator,
                                robinhoodClient,
                                userConfig.projectConfig.accountCode,
                                userConfig.brokerClientConfig.ROBINHOOD_CLIENT['username'],
                                userConfig.brokerClientConfig.ROBINHOOD_CLIENT['password'])
            t.connectWrapper()
        elif brokerClientName == BrokerClientName.TD:
            from broker_client_factory.TdAmeritrade import TDClient
            from .BrokerClient_TdAmeritrade import BrokerClientTdAmeritrade
            tdClient = TDClient(userConfig.brokerClientConfig.TD_CLIENT['refreshToken'],
                                userConfig.brokerClientConfig.TD_CLIENT['apiKey'],
                                userConfig.brokerClientConfig.TD_CLIENT['refreshTokenCreatedOn'],
                                [userConfig.projectConfig.accountCode],
                                userConfig.log)
            t = BrokerClientTdAmeritrade()
            t.setup_this_client(userConfig,
                                userConfig.log,
                                userConfig.projectConfig.rootFolderPath,
                                userConfig.singleTrader,
                                userConfig.dataFromServer,
                                userConfig.timeGenerator,
                                tdClient,
                                userConfig.projectConfig.accountCode)
            t.connectWrapper()
        else:
            raise RuntimeError(__name__ + '::get_brokerClient: cannot handle brokerClientName = %s' % (brokerClientName,))
        _invoke_log(userConfig, 'get_brokerClient', 'created brokerClient=%s id=%s dataProvider=None is correct at the moment, setup_services will invoke later.' % (t.name, id(t)))
        if t.name == BrokerClientName.IBinsync:
            self._brokerClientFactoryDict[BrokerClientName.IB] = t
        self._brokerClientFactoryDict[t.name] = t
        return t
