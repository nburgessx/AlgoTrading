# -*- coding: utf-8 -*-
import datetime as dt
import os
import time
import logging

import broker_service_factory
import market_calendar_factory
from BasicPyLib.repeater import Repeater, Event
from BasicPyLib.sendEmail import IbpyEmailClient
from BasicPyLib.simpleLogger import SimpleLogger
from IBridgePy.constants import TraderRunMode, LogLevel, BrokerClientName, LiveBacktest
from models.AccountInfo import UpdateAccountValueRecord
from models.Data import DataFromServer
from models.SingleTrader import SingleTrader


class MarketManager(object):
    def __init__(self, userConfig):
        """
        Change to this way because MarketManager is used to run multiple fileNames
        Trader is not combined into userConfig because trader.funcs needs to be exposed to users
        If dataProvider is IB or other real dataProvider, a client to the dataProvider is needed.
        In this case, userConfig_dataProvider is needed to build a dataProvider that has a valid dataProviderClient
        """
        self._userConfig = userConfig
        self._log = userConfig.log
        self.trader = userConfig.trader
        self.showTimeZone = userConfig.projectConfig.showTimeZone
        self.repBarFreq = userConfig.projectConfig.repBarFreq
        self.accountCode = userConfig.projectConfig.accountCode
        self.repeaterConfig = userConfig.repeaterConfig
        self.marketManagerConfig = userConfig.marketManagerConfig
        self.traderConfig = userConfig.traderConfig
        self.rootFolderPath = userConfig.projectConfig.rootFolderPath
        self._liveOrBacktest = userConfig.projectConfig.liveOrBacktest
        self._marketCalendar = userConfig.marketCalendar
        self._log.debug(__name__ + '::__init__')

        self.lastCheckConnectivityTime = dt.datetime.now()
        self.numberOfConnection = 0

        self._autoReconnectPremium = userConfig.projectConfig.autoReconnectPremium
        self._autoReconnectFreq = userConfig.projectConfig.autoReconnectFreq

        self._balanceLog = userConfig.balanceLog
        self._transactionLog = userConfig.transactionLog
        self._userLog = userConfig.userLog

    def run(self, run_init=True):
        self._log.debug(__name__ + '::run: START, runMode=%s' % (self.traderConfig.runMode,))
        self.trader.connect()
        # Functions just run once here
        if run_init:
            self.trader.initialize_Function()

        if self.traderConfig.runMode in [TraderRunMode.REGULAR, TraderRunMode.SUDO_RUN_LIKE_QUANTOPIAN]:
            self.run_regular()
        elif self.traderConfig.runMode in [TraderRunMode.RUN_LIKE_QUANTOPIAN]:
            self.run_q()
        elif self.traderConfig.runMode == TraderRunMode.HFT:
            self.run_hft()
        else:
            self._log.error(__name__ + '::run: cannot handle traderConfig.runMode=%s' % (self.traderConfig.runMode,))
        self._balanceLog.write_all_messages_to_file()
        self._transactionLog.write_all_messages_to_file()
        self._log.write_all_messages_to_file()
        self._userLog.write_all_messages_to_file()
        self._log.info(f'{self._userConfig.projectConfig.fileName} END')

    def run_regular(self):
        """
        Run handle_data every second(configurable), ignoring any market time or holidays
        :return:
        """
        self._log.debug(__name__ + '::run_regular')
        re = Repeater(self.repeaterConfig.slowdownInSecond,
                      self.trader.get_next_time,
                      self.trader.getWantToEnd,
                      self._log)

        # sequence matters!!! First scheduled, first run.
        repeater1 = Event.RepeatedEvent(self.marketManagerConfig.baseFreqOfProcessMessage, self.trader.processMessages)
        repeater2 = Event.RepeatedEvent(self.repBarFreq, self.trader.repeat_Function)
        re.schedule_event(repeater1)
        re.schedule_event(repeater2)
        if self._autoReconnectPremium:
            repeater3 = Event.RepeatedEvent(self._autoReconnectFreq, self.trader.get_heart_beats)
            re.schedule_event(repeater3)
        # for ct in re.repeatedEvents:
        #    print(ct, re.repeatedEvents[ct])
        re.repeat()  # trader.setWantToEnd will call disconnect

    def run_q(self):
        """
        Run handle_data every minute when US market is open, observing market time or holidays configured by setting.MARKET_MANAGER.marketName
        :return:
        """
        self._log.debug(__name__ + '::run_q')
        re = Repeater(self.repeaterConfig.slowdownInSecond,
                      self.trader.get_next_time,
                      self.trader.getWantToEnd,
                      self._log)
        # sequence matters!!! First scheduled, first run.
        repeater1 = Event.RepeatedEvent(self.marketManagerConfig.baseFreqOfProcessMessage, self.trader.processMessages)
        repeater2 = Event.RepeatedEvent(self.repBarFreq,
                                        self.trader.repeat_Function,
                                        passFunc=self._marketCalendar.is_market_open_at_this_moment)

        # When a new day starts, check if the new day is a trading day.
        # If it is a trading day, check marketOpenTime and marketCloseTime
        # repeater3 = Event.ConceptEvent(TimeConcept.NEW_DAY, self._check_at_beginning_of_a_day)

        # 9:25 EST to run before_trading_start(context, dataFromServer)
        repeater4 = Event.SpotTimeEvent(self.marketManagerConfig.beforeTradeStartHour,
                                        self.marketManagerConfig.beforeTradeStartMinute,
                                        onSecond=0,
                                        do_something=self.trader.before_trade_start_Function,
                                        passFunc=self._marketCalendar.isTradingDay)  # 09:25 to run before_trading_start, a quantopian style function

        if self._liveOrBacktest == LiveBacktest.LIVE:
            # print('live')
            re.schedule_event(repeater1)  # for live trade, run processMessage BEFORE handle_data because IBridgePy needs update data from broker server
            re.schedule_event(repeater2)
            # re.schedule_event(repeater3)
            re.schedule_event(repeater4)
            if self._autoReconnectPremium:
                repeater5 = Event.RepeatedEvent(60, self.trader.get_heart_beats)
                re.schedule_event(repeater5)
        elif self._liveOrBacktest == LiveBacktest.BACKTEST:
            # print('backtest')
            re.schedule_event(repeater2)  # for backtest, run processMessage AFTER handle_data because Backtester needs to simulate handling orders.
            re.schedule_event(repeater1)
            # re.schedule_event(repeater3)
            re.schedule_event(repeater4)
        else:
            self._log.error('Cannot handle self._liveOrBacktest=%s' % (self._liveOrBacktest,))
            exit()
        re.repeat()  # trader.setWantToEnd will call disconnect

    def run_hft(self):
        re = Repeater(self.repBarFreq,
                      self.trader.get_next_time,
                      self.trader.getWantToEnd,
                      self._log)
        # sequence matters!!! First scheduled, first run.
        repeater1 = Event.HftEvent(self.trader.processMessages)
        repeater2 = Event.HftEvent(self.trader.repeat_Function)
        re.schedule_event(repeater1)
        re.schedule_event(repeater2)
        re.repeat()  # trader.setWantToEnd will call disconnect

    def ingest_historical_data(self, histIngestionPlan):
        self._log.info('####     Data ingestion starts    ####')
        self.trader.getBrokerService().getBrokerClient().getDataProvider().ingest_hists(histIngestionPlan)
        self._log.info('####     Data ingestion COMPLETED    ####')

    def terminate(self):
        self.trader.terminate_all_clients()


def setup_services(userConfig, trader):
    """
    stay here to avoid cyclic imports
    trader  <----> brokerService -----> brokerClient <-----> dataProvider
             ----> dataProviderService
    """
    logging.debug(f'{__name__}::setup_services')
    logInMemory = False
    if userConfig.projectConfig.liveOrBacktest == LiveBacktest.BACKTEST:
        logInMemory = True
    dateTimeStr = time.strftime("%Y_%m_%d_%H_%M_%S")
    sysLogFileName = 'TraderLog_' + time.strftime("%Y-%m-%d") + '.txt'
    # userLog is for the function of record (). User will use it for any reason.
    userConfig.userLog = SimpleLogger(filename='userLog_' + dateTimeStr + '.txt',
                                      logLevel='NOTSET',
                                      folderPath=os.path.join(userConfig.projectConfig.rootFolderPath, 'Output'),
                                      addTime=False)
    userConfig.log = SimpleLogger(sysLogFileName, userConfig.projectConfig.logLevel,
                                  logInMemory=logInMemory,
                                  addTime=not logInMemory)
    userConfig.balanceLog = SimpleLogger(filename='BalanceLog_' + dateTimeStr + '.txt',
                                         logLevel='NOTSET',
                                         addTime=False,
                                         folderPath=os.path.join(userConfig.projectConfig.rootFolderPath, 'Output'),
                                         logInMemory=logInMemory)
    userConfig.transactionLog = SimpleLogger(filename='TransactionLog_' + dateTimeStr + '.txt',
                                             logLevel='NOTSET',
                                             addTime=False,
                                             folderPath=os.path.join(userConfig.projectConfig.rootFolderPath, 'Output'),
                                             logInMemory=logInMemory)

    # TimeGenerator instance will be used to build brokerClient and brokerService so that it needs to be created first.
    userConfig.timeGenerator = userConfig.timeGeneratorFactory.get_timeGenerator(userConfig.timeGeneratorConfig)
    userConfig.singleTrader = SingleTrader(userConfig.log)
    userConfig.dataFromServer = DataFromServer()

    # This brokerClient is responsible for trading
    # must before dataProvider, dataProvider of IB, TD, Robinhood must have a brokerClient
    userConfig.brokerClient = userConfig.brokerClientFactory.get_brokerClient_by_userConfig(userConfig)

    userConfig.brokerService = broker_service_factory.get_brokerService(userConfig)

    # dataProvider does not exist when brokerClient is created but dataProvider_localFile do need a brokerClient
    userConfig.dataProvider = userConfig.dataProviderFactory.get_dataProvider_by_userConfig(userConfig)
    if userConfig.brokerClient.name in [BrokerClientName.LOCAL]:
        userConfig.brokerClient._dataProvider = userConfig.dataProvider



    # default dataProviderService is as same as brokerService.
    # dataProviderService is used in Trader to provide data(real time price and hist)
    # brokerService_Local is able to provide data as long as it is setup correctly, which means correct brokerClient and correct dataProvider.
    # Do NOT change to data_provider_factory::dataProvider because brokerService is high abstraction and don't need to handle broker communications
    # Exception: !!!
    # When brokerService is not expected to provide data, dataProviderService will be used.
    # For example, don't have data subscription at IB and want to use TD to get real time data and hist data
    # In the above use case, userConfig.projectConfig.dataProviderName can be used.
    userConfig.dataProviderService = userConfig.brokerService

    userConfig.marketCalendar = market_calendar_factory.get_marketCalendar(userConfig.marketManagerConfig.marketName)
    userConfig.emailClient = IbpyEmailClient(userConfig.emailClientConfig.IBRIDGEPY_EMAIL_CLIENT['apiKey'], userConfig.log)

    # trader is not required when only brokerService is needed for providing data.
    if trader:
        trader.update_from_userConfig(userConfig)
        userConfig.trader = trader

    if userConfig.projectConfig.logLevel in [LogLevel.DEBUG, LogLevel.NOTSET]:
        print(userConfig)
    return userConfig


def setup_backtest_account_init_info(userConfig):
    # balanceLog is for backtesting daily portfolio tracking
    brokerName = userConfig.projectConfig.brokerName
    accountCode = userConfig.projectConfig.accountCode
    initValue = float(userConfig.backtesterConfig.initPortfolioValue)
    userConfig.singleTrader.set_updateAccountValue(brokerName, accountCode,
                                                   UpdateAccountValueRecord('TotalCashValue', initValue, 'USD',
                                                                            accountCode))
    userConfig.singleTrader.set_updateAccountValue(brokerName, accountCode,
                                                   UpdateAccountValueRecord('NetLiquidation', initValue, 'USD',
                                                                            accountCode))
    userConfig.singleTrader.set_updateAccountValue(brokerName, accountCode,
                                                   UpdateAccountValueRecord('GrossPositionValue', 0.00, 'USD',
                                                                            accountCode))
