# coding=utf-8
from sys import exit

import pytz

from BasicPyLib.Printable import Printable
from IBridgePy.constants import LogLevel, TraderRunMode, DataProviderName, MarketName, TimeGeneratorType


class Input(Printable):
    def __init__(self):
        pass


def validate_user_manual_input(globalsV):
    """
    This function does not work yet. The problem is that user can write any arbitrary variables in RUN_ME/TEST_ME.
    Not good solution check the validity of user inputs yet.
    :param globalsV:
    :return:
    """
    acceptedValues = ['accountCode', 'repBarFreq', 'startTime', 'endTime', 'fileName', 'backtest', 'freq',
                      'customSpotTimeList', 'handle_data', 'initialize', 'before_trading_start', 'histIngestionPlan', 'logLevel', 'runMode', 'dataProviderName', 'marketName', 'timeGeneratorType']
    for item in globalsV:
        if isinstance(globalsV[item], str) or isinstance(globalsV[item], int) or isinstance(globalsV[item], list) or isinstance(globalsV[item], dict) or isinstance(globalsV[item], tuple):
            if '__' not in item and item not in acceptedValues:
                print(__name__ + '::validate_user_manual_input: EXIT, cannot handle input=%s value=%s type=%s from RUN_ME/TEST_ME.' % (item, globalsV[item], type(globalsV[item])))
                print('Hint: 1. Check the spelling of the input.')
                print('Hint: 2. Add the input into settings.py instead of manually adding values in RUN_ME/TEST_ME.')
                exit()


def get_user_input_and_set_default_values(globalsV):
    # print(globalsV)
    userInput = _get_user_input(globalsV)
    _set_default_values_for_user_input(userInput)
    return userInput


def _set_default_values_for_user_input(userInput):
    if not hasattr(userInput, 'initialize'):
        userInput.initialize = (lambda x, y: None)
    if not hasattr(userInput, 'handle_data'):
        userInput.handle_data = (lambda x, y: None)
    if not hasattr(userInput, 'before_trading_start'):
        userInput.before_trading_start = (lambda x, y: None)


def _get_user_input(globalsV):
    """
    Get singleTrader's input and store them in an Input object.
    by setting an attribute and a value.
    For example,
    user_input.accountCode = 'testAccountCode'
    user_input.repBarFreq = 60
    :param globalsV: a dictionary, input by the build-in globals()
    :return: Input object
    """
    user_input = Input()

    for item in ['TimeGeneratorType']:
        if item in globalsV:
            print(__name__ + '::_get_user_input: EXIT, it should be timeGeneratorType, input=TimeGeneratorType')
            exit()

    # These values are the values that users can defined in RUN_ME.py. Optional
    # They are Non enum inputs.
    for item in ['accountCode', 'repBarFreq', 'startTime', 'endTime', 'fileName', 'backtest', 'freq',
                 'customSpotTimeList',
                 'handle_data', 'initialize', 'before_trading_start', 'histIngestionPlan', '__file__']:
        if item in globalsV:
            setattr(user_input, item, globalsV[item])

    # These values are the values that users can defined in RUN_ME.py. Optional
    # All of them needs transformation!!!
    for item in ['logLevel', 'runMode', 'dataProviderName', 'marketName', 'timeGeneratorType', 'showTimeZone']:
        if item in globalsV:
            if item == 'logLevel':
                setattr(user_input, item, LogLevel().get(globalsV[item], 'configTools::_get_user_input'))
            if item == 'runMode':
                setattr(user_input, item, TraderRunMode().get(globalsV[item], 'configTools::_get_user_input'))
            if item == 'dataProviderName':
                setattr(user_input, item, DataProviderName().get(globalsV[item], 'configTools::_get_user_input'))
            if item == 'marketName':
                setattr(user_input, item, MarketName().get(globalsV[item], 'configTools::_get_user_input'))
            if item == 'timeGeneratorType':
                setattr(user_input, item, TimeGeneratorType().get(globalsV[item], 'configTools::_get_user_input'))
            if item == 'showTimeZone':
                setattr(user_input, item, pytz.timezone(globalsV[item]))
    return user_input
