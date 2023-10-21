# coding=utf-8
from Config.config_defs import UserConfig
from IBridgePy.constants import TimeGeneratorType
from configuration import _build_config


def build_active_IBridgePy_plus(accountCode=None):
    userConfig = UserConfig().get_config('IBinsync')
    if accountCode:
        userConfig.projectConfig.accountCode = accountCode
    userConfig.projectConfig.logLevel = 'INFO'
    userConfig = _build_config(userConfig)
    userConfig.trader.display_all()
    return userConfig.trader


def build_active_TD_trader(accountCode=None):
    userConfig = UserConfig.get_config('TD')
    userConfig.projectConfig.logLevel = 'INFO'
    if accountCode:
        userConfig.projectConfig.accountCode = accountCode
    userConfig = _build_config(userConfig)
    userConfig.trader.connect()
    return userConfig.trader


def build_trader_for_backtest():
    userConfig = UserConfig.get_config('BACKTEST')
    userConfig.projectConfig.logLevel = 'INFO'
    userConfig.timeGeneratorConfig.timeGeneratorType = TimeGeneratorType.LIVE
    userConfig = _build_config(userConfig)
    userConfig.trader.connect()
    return userConfig.trader
