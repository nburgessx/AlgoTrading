# coding=utf-8
import os
import time
import traceback
import logging

# noinspection PyUnresolvedReferences
from BasicPyLib.BasicTools import roundToMinTick, get_system_info
from Config.config_defs import UserConfig
# noinspection PyUnresolvedReferences
from IBridgePy.IbridgepyTools import superSymbol, check_user_sys_compatibility
from IBridgePy.MarketManagerBase import MarketManager, setup_services, setup_backtest_account_init_info
# noinspection PyUnresolvedReferences
from IBridgePy.OrderTypes import MarketOrder, StopOrder, LimitOrder, StopLimitOrder, TrailStopLimitOrder, \
    TrailStopOrder, MarketOnCloseOrder
from IBridgePy.Trader import Trader
from IBridgePy.constants import LiveBacktest, DataProviderName, LogLevel, TraderRunMode
# noinspection PyUnresolvedReferences
from IBridgePy.quantopian import date_rules, time_rules, calendars
from broker_client_factory.CustomErrors import CustomError
from broker_client_factory.CustomErrors import ErrorCode

check_user_sys_compatibility()


def test_me(fileName, userManualInput, userConfig=None):
    if not userConfig:
        userConfig = UserConfig.get_config('BACKTEST')
    # print(__name__ + '::test_me: id of userConfig=%s' % (id(userConfig),))
    userConfig = _build_config(userConfig, userManualInput, fileName)
    _finally_run(userConfig, LiveBacktest.BACKTEST)


def _helper(userConfig, userManualInput, fileName):
    userConfig = _build_config(userConfig, userManualInput, fileName)
    if userConfig.projectConfig.brokerServiceName != userConfig.projectConfig.dataProviderName:
        print('!!! Data provider is %s but the broker service is %s. They are NOT same. !!!' % (userConfig.projectConfig.dataProviderName, userConfig.projectConfig.brokerServiceName))
        userConfig = _setup_dataProviderService(userConfig)
    _finally_run(userConfig, LiveBacktest.LIVE)


def run_me_at_robinhood(fileName, userManualInput, userConfig=None):
    if not userConfig:
        userConfig = UserConfig.get_config('ROBINHOOD')
    _helper(userConfig, userManualInput, fileName)


def run_me_at_td_ameritrade(fileName, userManualInput, userConfig=None):
    if not userConfig:
        userConfig = UserConfig.get_config('TD')
    _helper(userConfig, userManualInput, fileName)


def run_me_at_HFT(fileName, userManualInput):
    userConfig = UserConfig.get_config('HFT')
    userConfig.traderConfig.runMode = TraderRunMode.HFT  # Prevent that runMode is overridden by settings.py
    _helper(userConfig, userManualInput, fileName)


def run_me(fileName, userManualInput, userConfig=None):
    logging.debug(f'{__name__}::run_me')
    run_init = True
    if userConfig is None:
        userConfig = UserConfig.get_config('IB')
    userConfig = _build_config(userConfig, userManualInput, fileName)
    if userConfig.projectConfig.brokerServiceName != userConfig.projectConfig.dataProviderName:
        print('!!! Data provider is %s but the broker service is %s. They are NOT same. !!!' % (userConfig.projectConfig.dataProviderName, userConfig.projectConfig.brokerServiceName))
        userConfig = _setup_dataProviderService(userConfig)
    autoReconnectPremium = userConfig.projectConfig.autoReconnectPremium
    c = MarketManager(userConfig)

    while True:
        try:
            c.run(run_init=run_init)
            break
        except CustomError as e:
            if e.error_code in [509, 504, 502, 10141, ErrorCode.ERR_LOST_HEART_BEAT.code] and autoReconnectPremium:
                # errorCode:509 errorId:-1 errorMessage=Exception caught while reading socket - Broken pipe
                # errorCode=509 errorMessage=Exception caught while reading socket - Connection reset by peer -- Reason: Invoke connectWrapper() when there is connection already.
                # errorCode=509 errorMessage=Exception caught while reading socket - Connection reset by peer -- Reason 1: IB Gateway was turned off suddenly
                # errorCode:10141 errorId:-1 errorMessage=Paper trading disclaimer must first be accepted for API connection.
                # errorCode:509 errorId:-1 errorMessage=Exception caught while reading socket - Connection reset by peer
                # errorCode:509 errorId:-1 errorMessage=Exception caught while reading socket - Function not implemented
                # errorCode:502 errorId:-1 errorMessage=Couldn't connect to TWS.  Confirm that "Enable ActiveX and Socket Clients" is enabled on the TWS "Configure->API" menu.
                # errorCode=504 errorMessage=Not connected
                print('IBridgePy will sleep 10 seconds and reconnect again.')
                run_init = False
                time.sleep(10)
                userConfig.brokerClient.disconnectWrapper()
                userConfig.brokerClient = userConfig.brokerClientFactory.get_brokerClient_by_userConfig(userConfig, check_cache=False)
            else:
                break
        except (RuntimeError, Exception) as err:
            print(f'If you need help, please send email to IBridgePy@gmail.com. Terminate IBridgePy because error={err} {traceback.print_exc()}')
            break
    c.terminate()


def _setup_dataProviderService(userConfig):
    dataProviderName = userConfig.projectConfig.dataProviderName
    if dataProviderName == DataProviderName.TD:
        userConfigDataProvider = UserConfig.get_config('TD')
    elif dataProviderName == DataProviderName.IB:
        userConfigDataProvider = UserConfig.get_config('IB')
    elif dataProviderName == DataProviderName.ROBINHOOD:
        userConfigDataProvider = UserConfig.get_config('ROBINHOOD')
    elif dataProviderName in [DataProviderName.RANDOM, DataProviderName.LOCAL_FILE]:
        userConfigDataProvider = UserConfig.get_config('LOCAL')
    else:
        raise RuntimeError('cannot handle userConfig.projectConfig.dataProviderName=%s' % (dataProviderName,))
    userConfigDataProvider.projectConfig.logLevel = LogLevel.ERROR
    userConfigDataProvider.projectConfig.dataProviderName = dataProviderName  # Do NOT delete. This is not necessary because settings.py is applied but just make sure it is effective
    userConfigDataProvider.brokerClientFactory = userConfig.brokerClientFactory  # userConfig.brokerClientFactory is used as a singleton manager so that userConfigDataProvider will not create extra copy of brokerClients
    userConfigDataProvider.timeGeneratorFactory = userConfig.timeGeneratorFactory  # make sure timeGenerator is singleton
    userConfigDataProvider = setup_services(userConfigDataProvider, None)
    userConfigDataProvider.dataProviderService.setAsDataProviderService()  # set brokerService instance as a dataProviderService instance
    userConfigDataProvider.dataProviderService.getBrokerClient().setAsDataProviderClient()
    userConfig.trader.dataProviderService = userConfigDataProvider.dataProviderService  # use the created dataProviderService as the dataProviderService of the trader
    userConfig.dataProviderService = userConfigDataProvider.dataProviderService  # use the created dataProviderService as the dataProviderService of the main userConfig
    return userConfig


# noinspection DuplicatedCode
def _build_config(userConfig, userManualInput=None, fileName=None):
    """

    :param userConfig: Config::config_defs::UserConfig
    :param userManualInput: a dictionary, key=variable name, value= variable value, Should be provided by global() or local()
    :param fileName: the current strategy file name
    :return: modified userConfig
    """
    logging.debug(f'{__name__}::_build_config')
    # print(userManualInput)
    # exit()
    # print(userConfig)
    trader = Trader()  # To setup trader, trader.update_from_userConfig is needed

    # the following must happen before     globals().update(locals())
    cancel_all_orders = trader.cancel_all_orders
    cancel_order = trader.cancel_order
    close_all_positions = trader.close_all_positions
    close_all_positions_except = trader.close_all_positions_except
    count_positions = trader.count_positions
    create_order = trader.create_order
    display_all = trader.display_all
    display_orderStatus = trader.display_orderStatus
    display_positions = trader.display_positions
    end = trader.setWantToEnd
    get_5_second_real_time_bar = trader.get_5_second_real_time_bar
    get_datetime = trader.get_datetime
    get_all_open_orders = trader.get_all_open_orders
    get_all_orders = trader.get_all_orders
    get_all_positions = trader.get_all_positions
    get_contract_details = trader.get_contract_details
    get_ibpy_expiry_in_days = trader.get_ibpy_expiry_in_days
    get_open_orders = trader.get_open_orders
    get_option_info = trader.get_option_info
    get_order = trader.get_order
    get_order_status = trader.get_order_status
    get_position = trader.get_position
    get_scanner_results = trader.get_scanner_results
    get_TD_access_token_expiry_in_days = trader.get_TD_access_token_expiry_in_days
    hold_any_position = trader.hold_any_position
    isEarlyClose = trader.isEarlyClose
    isTradingDay = trader.isTradingDay
    modify_order = trader.modify_order
    order = trader.order
    order_status_monitor = trader.order_status_monitor
    order_target = trader.order_target
    order_target_percent = trader.order_target_percent
    order_target_value = trader.order_target_value
    order_percent = trader.order_percent
    order_value = trader.order_value
    place_combination_orders = trader.place_combination_orders
    place_order_with_stoploss = trader.place_order_with_stoploss
    place_order_with_stoploss_takeprofit = trader.place_order_with_stoploss_takeprofit
    place_order_with_takeprofit = trader.place_order_with_takeprofit
    request_historical_data = trader.request_historical_data
    rebalance_portfolio = trader.rebalance_portfolio
    record = trader.record
    schedule_function = trader.schedule_function
    send_email = trader.send_email
    show_account_info = trader.show_account_info
    show_real_time_price = trader.show_real_time_price
    show_real_time_size = trader.show_real_time_size
    show_timestamp = trader.show_timestamp
    symbol = trader.symbol
    symbols = trader.symbols

    # open function in py2 and py3 are different.
    # UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 1035: character maps to <undefined> (Question id : 728)
    # The root cause of the above error is that some strange characters show up in the imported files.
    # Only happens in Windows Py3 because open in py3 does not use default utf-8 decoder but it uses the default encoder set by windows.
    # The solution is not to use strange characters.
    if fileName:  # It is fine without fileName. It will be used in testing framework
        fullFileName = os.path.join(userConfig.projectConfig.rootFolderPath, 'Strategies', fileName)
        with open(fullFileName) as f:
            script = f.read()
        # noinspection PyRedundantParentheses
        code_block = compile(script, fullFileName, 'exec')
        exec(code_block)

    # print(globals())
    # print(locals())

    # If without this line, handle_data and initialize would be local variables
    # but the IBridgePy build-in functions, such as cancel_all_orders, order_target and get_positions, are all global variables
    # If without this line, error jumps out.
    # NameError: global name 'cancel_all_orders' is not defined
    # update is to merger two dictionaries
    globals().update(locals())

    if userManualInput:
        locals().update(userManualInput)

    # setup_service happens inside here.
    # After this line, all instances should be ready to use in userConfig
    userConfig.prepare_userConfig_with_trader(trader, locals())

    # print(userConfig)
    # exit()
    return userConfig


def _finally_run(userConfig, liveOrTest, run_init=True):
    if liveOrTest == LiveBacktest.LIVE:
        c = MarketManager(userConfig)
        c.run(run_init=run_init)
        c.terminate()
    elif liveOrTest == LiveBacktest.BACKTEST:
        c = MarketManager(userConfig)
        setup_backtest_account_init_info(userConfig)
        c.ingest_historical_data(userConfig.projectConfig.histIngestionPlan)
        c.run(run_init=run_init)
        c.terminate()
