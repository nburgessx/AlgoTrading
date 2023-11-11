# -*- coding: utf-8 -*-
"""
All rights reserved.
@author: IBridgePy@gmail.com
"""
from IBridgePy.constants import DataProviderName, LogLevel, BrokerClientName


# Put here to avoid cyclic import
def _invoke_log(userConfig, caller, message):
    if userConfig.projectConfig.logLevel in [LogLevel.DEBUG, LogLevel.NOTSET]:
        print(__name__ + '::%s:%s' % (caller, message))


class DataProviderFactory(object):
    def __init__(self):
        self._dataProviderFactoryDict = {}

    def __str__(self):
        if not self._dataProviderFactoryDict:
            return '{Empty dict}'
        ans = '{'
        for key in self._dataProviderFactoryDict:
            ans += '%s:%s ' % (key, self._dataProviderFactoryDict[key])
        ans = ans[:-1] + '}'
        return ans

    def _find_dataProvider_in_cache(self, dataProviderName):
        t = None
        if dataProviderName in self._dataProviderFactoryDict:
            t = self._dataProviderFactoryDict[dataProviderName]
            return t
        return t

    def get_dataProvider_by_userConfig(self, userConfig):
        dataProviderName = userConfig.projectConfig.dataProviderName
        _invoke_log(userConfig, 'get_dataProvider_by_name', dataProviderName)
        t = self._find_dataProvider_in_cache(dataProviderName)
        if t:
            return t
        t = get_dataProvider(userConfig)
        self._dataProviderFactoryDict[dataProviderName] = t
        return t

    def get_dataProvider_by_name(self, dataProviderName, userConfig):
        t = self._find_dataProvider_in_cache(dataProviderName)
        if t:
            # print(__name__ + '::get_dataProvider_by_name: found %s in cache.' % (dataProviderName,))
            return t
        t = get_dataProvider(userConfig, dataProviderName)
        self._dataProviderFactoryDict[dataProviderName] = t
        # print(__name__ + '::get_dataProvider_by_name: created %s in cache.' % (dataProviderName,))
        return t


def get_dataProvider(userConfig, dataProviderName=None):
    if dataProviderName is None:
        name = userConfig.projectConfig.dataProviderName
        if name is None:
            return None
    else:
        name = dataProviderName
    # print(__name__ + '::get_dataProvider: name=%s' % (name,))
    if name == DataProviderName.LOCAL_FILE:
        from .dataProvider_localFile import LocalFile
        t = LocalFile(userConfig, userConfig.log, userConfig.projectConfig.useColumnNameWhenSimulatedByDailyBar)
    elif name == DataProviderName.RANDOM:
        from .dataProvider_random import RandomDataProvider
        t = RandomDataProvider(userConfig, userConfig.log)
    elif name == DataProviderName.IB:
        from .dataProvider_IB import IB
        t = IB(userConfig, userConfig.log, userConfig.projectConfig.useColumnNameWhenSimulatedByDailyBar)
    elif name == DataProviderName.TD:
        from .dataProvider_TD import TD
        t = TD(userConfig, userConfig.log, userConfig.projectConfig.useColumnNameWhenSimulatedByDailyBar)
    elif name == DataProviderName.ROBINHOOD:
        from .dataProvider_Robinhood import Robinhood
        t = Robinhood(userConfig, userConfig.log, userConfig.projectConfig.useColumnNameWhenSimulatedByDailyBar)
    elif name == DataProviderName.IBRIDGEPY:
        from .dataProvider_IBridgePy import IBridgePy
        t = IBridgePy(userConfig, userConfig.log, userConfig.emailClientConfig.IBRIDGEPY_EMAIL_CLIENT['apiKey'], userConfig.projectConfig.useColumnNameWhenSimulatedByDailyBar)
    elif name == DataProviderName.YAHOO_FINANCE:
        from .dataProvider_YahooFinance import YahooFinance
        t = YahooFinance(userConfig, userConfig.log, userConfig.projectConfig.useColumnNameWhenSimulatedByDailyBar)
    else:
        raise RuntimeError(__name__, 'cannot handle dataProviderName=%s' % (name,))

    # These data providers do not need a brokerClient at all.
    if t.name not in [DataProviderName.RANDOM, DataProviderName.LOCAL_FILE, DataProviderName.IBRIDGEPY, DataProviderName.YAHOO_FINANCE]:
        if t.name != t.get_dataProviderClient().name:
            if t.name == DataProviderName.IB:
                if t.get_dataProviderClient().name != BrokerClientName.IBinsync:
                    raise RuntimeError('dataProviderName=%s dataProviderClientName=%s !They are not same!' % (t.name, t.get_dataProviderClient().name))
            else:
                raise RuntimeError('dataProviderName=%s dataProviderClientName=%s !They are not same!' % (t.name, t.get_dataProviderClient().name))

    _invoke_log(userConfig, 'get_dataProvider', 'created dataProvider=%s' % (t,))
    return t
