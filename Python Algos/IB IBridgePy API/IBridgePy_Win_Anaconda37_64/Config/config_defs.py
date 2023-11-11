# coding=utf-8
import importlib
from sys import exit
import logging

from BasicPyLib.BasicTools import isAllLettersCapital
from BasicPyLib.Printable import PrintableII, Printable
# noinspection PyUnresolvedReferences
from Config import base_settings
from Config.configTools import get_user_input_and_set_default_values
from IBridgePy.MarketManagerBase import setup_services
from IBridgePy.TimeGenerator import TimeGeneratorFactory
from IBridgePy.constants import DataProviderName, LiveBacktest, TraderRunMode, TimeGeneratorType, MarketName, BrokerName
from broker_client_factory.BrokerClient_factory import BrokerClientFactory
from data_provider_factory.data_provider_factory import DataProviderFactory

"""
To create a new config
step 1: create a class like MARKET_MANAGER_Config; the format must be XXX_Config or XXX_XXX_Config
step 2: in base_setting.py add setting values as dictionary, naming must be XXX or XXX_XXX. It must to add all possible values and give default values
step 3: If it is user input setting, put default value for user in setting.py
step 4: If it needs special config other than base, add something like Config/backtest_settings.py, naming must be xxxx_settings.py
Override sequence: Config::base_settings -> Config::xx_settings -> projectRoot::settings -> config values in strategy file -> manually input in RUN_ME.py as Input() object
"""


class Config(PrintableII):
    def __init__(self, dict_settings):
        for key in dict_settings:
            setattr(self, key, dict_settings[key])

    def override(self, settings, settingFileName):
        for key in settings:
            # TODO: The whole part is due to IB_Client is a dict, not a XXX_config class
            if isinstance(settings[key], dict):
                originalValues = None
                try:
                    originalValues = getattr(self, key)
                except AttributeError as e:
                    print(__name__ + '::override: EXIT, %s. Hint: Check Config::base_settings if it has the attribute.' % (e,))
                    exit()
                newValueDict = settings[key]
                for k in newValueDict:
                    if k in originalValues:
                        originalValues[k] = newValueDict[k]
                    else:
                        print(__name__ + '::override: EXIT, key=%s in the file of <%s.py> does not exist in Config::base_settings.py' % (k, settingFileName))
                        exit()
            else:
                self.set_value(key, settings[key], settingFileName)
        return self

    def set_value(self, fieldName, value, settingName):
        """

        :param fieldName:
        :param value:
        :param settingName: string, used to display the fileName/source of the settings
        :return:
        """
        if hasattr(self, fieldName):
            setattr(self, fieldName, value)
        else:
            print(__name__ + '::set_value: class=%s key=%s settingFileName=%s does not exist.' % (self.__class__, fieldName, settingName))
            print('base_config: %s' % (self,))
            exit()


# noinspection PyPep8Naming
class BACKTESTER_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class MARKET_MANAGER_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class REPEATER_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class TIME_GENERATOR_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class BROKER_SERVICE_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class PROJECT_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class TRADER_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class BROKER_CLIENT_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class EMAIL_CLIENT_Config(Config):
    def __init__(self, dict_settings):
        Config.__init__(self, dict_settings)


# noinspection PyPep8Naming
class UserConfigBase(Printable):  # should not be used directly
    def __init__(self):
        """
        For example, there is a file Config::hft_settings.py Then, a possible value of addOnSettings is "hft_settings"
        """
        # NEW config system
        # Keep them without self._xxx because these values will be used as self.userConfig.projectConfig as an example.
        self.projectConfig = None
        self.marketManagerConfig = None
        self.repeaterConfig = None
        self.backtesterConfig = None
        self.timeGeneratorConfig = None
        self.traderConfig = None
        self.brokerClientConfig = None
        self.emailClientConfig = None

        self.initialize_quantopian = None
        self.handle_data_quantopian = None
        self.before_trading_start_quantopian = None

        self.timeGenerator = None
        self.dataFromServer = None
        self.singleTrader = None
        self.trader = None
        self.dataProvider = None
        self.log = None
        self.userLog = None
        self.balanceLog = None
        self.transactionLog = None
        self.brokerService = None  # responsible for trading
        self.dataProviderService = None  # responsible for getting data if it is not expected to get data from brokerService
        self.brokerClient = None  # embedded into brokerService to get connected to broker to trade
        self.emailClient = None  # to send email out
        self.brokerClientFactory = BrokerClientFactory()  # to save all created brokerClient. key= brokerClientName value = brokerClient
        self.timeGeneratorFactory = TimeGeneratorFactory()
        self.dataProviderFactory = DataProviderFactory()

    def load_settings(self, str_settings):
        # If str_settings == 'settings'
        # Then, this line works like 'import setting' so that config values are imported
        module_settings = importlib.import_module(str_settings)

        # Iterate all of the module names added to the local namespace including all the existing ones as before
        for item in dir(module_settings):
            if isAllLettersCapital(item):
                if item == 'PROJECT':
                    self.projectConfig = PROJECT_Config(getattr(module_settings, item))
                elif item == 'MARKET_MANAGER':
                    self.marketManagerConfig = MARKET_MANAGER_Config(getattr(module_settings, item))
                elif item == 'BACKTESTER':
                    self.backtesterConfig = BACKTESTER_Config(getattr(module_settings, item))
                elif item == 'REPEATER':
                    self.repeaterConfig = REPEATER_Config(getattr(module_settings, item))
                elif item == 'TIME_GENERATOR':
                    self.timeGeneratorConfig = TIME_GENERATOR_Config(getattr(module_settings, item))
                elif item == 'TRADER':
                    self.traderConfig = TRADER_Config(getattr(module_settings, item))
                elif item == 'BROKER_CLIENT':
                    self.brokerClientConfig = BROKER_CLIENT_Config(getattr(module_settings, item))
                elif item == 'EMAIL_CLIENT':
                    self.emailClientConfig = EMAIL_CLIENT_Config(getattr(module_settings, item))
                else:
                    print(__name__ + '::load_settings: EXIT, cannot handle item=%s in %s.py' % (item, str_settings))
                    exit()
        return self

    def overrideBy(self, str_settings):
        module_settings = importlib.import_module(str_settings)
        for item in dir(module_settings):
            if isAllLettersCapital(item):
                if item == 'PROJECT':
                    self.projectConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'MARKET_MANAGER':
                    self.marketManagerConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'REPEATER':
                    self.repeaterConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'BACKTESTER':
                    self.backtesterConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'TIME_GENERATOR':
                    self.timeGeneratorConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'TRADER':
                    self.traderConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'BROKER_CLIENT':
                    self.brokerClientConfig.override(getattr(module_settings, item), str_settings)
                elif item == 'EMAIL_CLIENT':
                    self.emailClientConfig.override(getattr(module_settings, item), str_settings)
                else:
                    print(__name__ + '::overrideBy: EXIT, cannot handle item=%s in %s' % (item, str_settings))
                    exit()
        return self

    def overrideByConfigDict(self, dict_passedIn):
        fileName = dict_passedIn['fileName']
        for item in dict_passedIn:
            # print(__name__ + '::overrideByConfigDict: item=%s value=%s' % (item, dict_passedIn[item]))
            if item == 'PROJECT':
                self.projectConfig.override(dict_passedIn[item], fileName)
                print('special config from %s: item=%s value=%s' % (fileName, item, dict_passedIn[item]))
            elif item == 'MARKET_MANAGER':
                self.marketManagerConfig.override(dict_passedIn[item], fileName)
                print('special config from %s: item=%s value=%s' % (fileName, item, dict_passedIn[item]))
            elif item == 'REPEATER':
                self.repeaterConfig.override(dict_passedIn[item], fileName)
                print('special config from %s: item=%s value=%s' % (fileName, item, dict_passedIn[item]))
            elif item == 'TIME_GENERATOR':
                self.timeGeneratorConfig.override(dict_passedIn[item], fileName)
                print('special config from %s: item=%s value=%s' % (fileName, item, dict_passedIn[item]))
            elif item == 'TRADER':
                self.traderConfig.override(dict_passedIn[item], fileName)
                print('special config from %s: item=%s value=%s' % (fileName, item, dict_passedIn[item]))
            elif item == 'BROKER_CLIENT':
                self.brokerClientConfig.override(dict_passedIn[item], fileName)
                print('special config from %s: item=%s value=%s' % (fileName, item, dict_passedIn[item]))
            elif item == 'EMAIL_CLIENT':
                self.emailClientConfig.override(dict_passedIn[item], fileName)
                print('special config from %s: item=%s value=%s' % (fileName, item, dict_passedIn[item]))
            elif item == 'BACKTESTER':
                self.backtesterConfig.override(dict_passedIn[item], fileName)
                print('special config from %s: item=%s value=%s' % (fileName, item, dict_passedIn[item]))
            else:
                pass
                # print(__name__ + '::overrideByConfigDict: NO action for item=%s in %s' % (item, fileName))
        return self

    def validate_after_build_trader(self):
        logging.debug(f'{__name__}::validate_after_build_trader')
        if self.projectConfig.liveOrBacktest == LiveBacktest.BACKTEST:
            print('Backtester ignores order.tif=DAY and handles them as order.tif=GTC. We are working on this feature.')
            print(f'Simulate trading commission by settings.py --> BACKTESTER --> simulateCommission')

            if self.backtesterConfig.overrideValues is True:
                if self.traderConfig.runMode != TraderRunMode.RUN_LIKE_QUANTOPIAN:
                    self.traderConfig.runMode = TraderRunMode.RUN_LIKE_QUANTOPIAN
                    print('IBridgePy has reset the TRADER.runMode to RUN_LIKE_QUANTOPIAN for backtesting to save time!')

                if self.projectConfig.repBarFreq != 60:
                    self.projectConfig.repBarFreq = 60
                    print('IBridgePy has reset projectConfig.repBarFreq to 60 for backtesting!')

            if self.timeGeneratorConfig.timeGeneratorType == TimeGeneratorType.AUTO:
                if self.timeGeneratorConfig.startingTime is None or self.timeGeneratorConfig.endingTime is None:
                    print('Backtester in TimeGeneratorType.AUTO but staringTime=%s endingTime=%s They should not be None' % (self.timeGeneratorConfig.startingTime, self.timeGeneratorConfig.endingTime))
                    exit()

            if self.timeGeneratorConfig.timeGeneratorType == TimeGeneratorType.LIVE:
                print('WARNING: Backtester with a LIVE timeGenerator should be used to get historical data only.')

            if self.projectConfig.autoReconnectPremium:
                self.projectConfig.autoReconnectPremium = False
                print('WARNING: The feature of AutoReconnect is turned off under the backtesting mode.')

        if self.traderConfig.runMode in [TraderRunMode.RUN_LIKE_QUANTOPIAN, TraderRunMode.SUDO_RUN_LIKE_QUANTOPIAN]:
            if self.projectConfig.repBarFreq != 60:
                print('EXIT, projectConfig.repBarFreq=%s It should be 60 when traderConfig.runMode is either RUN_LIKE_QUANTOPIAN or SUDO_RUN_LIKE_QUANTOPIAN' % (self.projectConfig.repBarFreq,))
                exit()

        if self.projectConfig.dataProviderName in [DataProviderName.IB, DataProviderName.TD, DataProviderName.ROBINHOOD]:
            if self.dataProvider is None:
                raise RuntimeError('self.dataProviderClient in dataProvider_%s is None' % (self.projectConfig.dataProviderName,))

        assert(self.trader is not None)

    def load_userInput_to_userConfig(self, user_input):
        logging.debug(f'{__name__}::load_userInput_to_userConfig: user_input={user_input}')
        # No action to map from user_input to user_config
        for item in ['accountCode', 'repBarFreq', 'fileName', 'logLevel', 'dataProviderName', 'histIngestionPlan']:
            if hasattr(user_input, item):
                self.projectConfig.set_value(item, getattr(user_input, item), __name__ + '::load_userInput_to_userConfig')
        if hasattr(user_input, 'marketName'):
            self.marketManagerConfig.set_value('marketName', user_input.marketName, __name__ + '::load_userInput_to_userConfig')

        if hasattr(user_input, 'startTime'):
            self.timeGeneratorConfig.set_value('startingTime', user_input.startTime, __name__ + '::load_userInput_to_userConfig')

        if hasattr(user_input, 'endTime'):
            self.timeGeneratorConfig.set_value('endingTime', user_input.endTime, __name__ + '::load_userInput_to_userConfig')

        if hasattr(user_input, 'freq'):
            self.timeGeneratorConfig.set_value('freq', user_input.freq, __name__ + '::load_userInput_to_userConfig')

        if hasattr(user_input, 'timeGeneratorType'):
            self.timeGeneratorConfig.set_value('timeGeneratorType', user_input.timeGeneratorType, __name__ + '::load_userInput_to_userConfig')
            if user_input.timeGeneratorType == TimeGeneratorType.CUSTOM:
                if hasattr(user_input, 'customSpotTimeList'):
                    self.timeGeneratorConfig.set_value('custom', user_input.customSpotTimeList, __name__ + '::load_userInput_to_userConfig')
                else:
                    print(__name__ + '::load_input: EXIT, customSpotTimeList is empty.')
                    exit()

        if hasattr(user_input, 'runMode'):
            if user_input.runMode in [TraderRunMode.RUN_LIKE_QUANTOPIAN, TraderRunMode.SUDO_RUN_LIKE_QUANTOPIAN]:
                self.projectConfig.set_value('repBarFreq', 60, __name__ + '::load_userInput_to_userConfig')
                self.traderConfig.set_value('runMode', user_input.runMode, __name__ + '::load_userInput_to_userConfig')
                if user_input.runMode == TraderRunMode.SUDO_RUN_LIKE_QUANTOPIAN:
                    self.marketManagerConfig.set_value('marketName', MarketName.NONSTOP, __name__ + '::load_userInput_to_userConfig')

        self.initialize_quantopian = user_input.initialize
        self.handle_data_quantopian = user_input.handle_data
        self.before_trading_start_quantopian = user_input.before_trading_start

    def prepare_userConfig_with_trader(self, trader, globalsV):
        logging.debug(f'{__name__}::prepare_userConfig_with_trader')
        # If any config values are defined in the strategy file,
        # they will be applied to userConfig here
        self.overrideByConfigDict(globalsV)

        # User will manually input some values in RUN_ME.py
        # For example, accountCode = 'xxx' or logLevel = 'DEBUG'
        # These inputs are free text, instead of structured values in settings.py.
        # This way is easier for user and used for backward compatibility
        userInput = get_user_input_and_set_default_values(globalsV)

        # This part only merge userInput into userConfig and then build userConfig.
        # set many values in userConfig
        self.load_userInput_to_userConfig(userInput)

        if not self.projectConfig.accountCode:
            if self.projectConfig.brokerName == BrokerName.TD:
                if self.brokerClientConfig.TD_CLIENT['accountCode']:
                    accountCode = self.brokerClientConfig.TD_CLIENT['accountCode']
                    print('User does not specify an accountCode. IBridgePy uses %s from settings.py::BROKER_CLIENT::TD_CLIENT::accountCode' % (accountCode,))
                    self.projectConfig.accountCode = accountCode
                else:
                    exit('EXIT, projectConfig.accountCode is empty. Please go to settings.py --> BROKER_CLIENT --> TD_CLIENT --> accountCode.')

            elif self.projectConfig.brokerName == BrokerName.IB:
                if self.brokerClientConfig.IB_CLIENT['accountCode']:
                    accountCode = self.brokerClientConfig.IB_CLIENT['accountCode']
                    print('User does not specify an accountCode. IBridgePy uses %s from settings.py::BROKER_CLIENT::IB_CLIENT::accountCode' % (accountCode,))
                    self.projectConfig.accountCode = accountCode
                else:
                    exit('EXIT, projectConfig.accountCode is empty. Please go to settings.py --> BROKER_CLIENT --> IB_CLIENT --> accountCode.')

            elif self.projectConfig.brokerName == BrokerName.ROBINHOOD:
                if self.brokerClientConfig.ROBINHOOD_CLIENT['accountCode']:
                    accountCode = self.brokerClientConfig.ROBINHOOD_CLIENT['accountCode']
                    print('User does not specify an accountCode. IBridgePy uses %s from settings.py::BROKER_CLIENT::ROBINHOOD_CLIENT::accountCode' % (accountCode,))
                    self.projectConfig.accountCode = accountCode
                else:
                    exit('EXIT, projectConfig.accountCode is empty. Please go to settings.py --> BROKER_CLIENT --> ROBINHOOD_CLIENT --> accountCode.')

            elif self.projectConfig.brokerName == BrokerName.LOCAL:
                self.projectConfig.accountCode = 'dummyAccountCode'
            else:
                exit(__name__ + '::prepare_userConfig_with_trader: EXIT, cannot handle self.projectConfig.brokerName=%s' % (self.projectConfig.brokerName,))

        # cannot instantiate trader here because defined_functions user's input need to go after trader.
        setup_services(self, trader)  # set many values in userConfig
        self.validate_after_build_trader()


class UserConfig(object):
    @staticmethod
    def get_config(name):
        # Override sequence MATTERS!!!
        ans = None
        if name == 'BACKTEST':
            ans = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.backtest_settings').overrideBy('settings')
        elif name == 'HFT':
            ans = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.hft_settings').overrideBy('settings')
        elif name == 'ROBINHOOD':
            ans = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.robinhood_settings').overrideBy('settings')
        elif name == 'TD':
            ans = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.td_settings').overrideBy('settings')
        elif name == 'IB':
            ans = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.ib_settings').overrideBy('settings')
        elif name == 'IBinsync':
            ans = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.ibinsync_settings').overrideBy('settings')
        elif name == 'LOCAL':
            ans = UserConfigBase().load_settings('Config.base_settings').overrideBy('Config.localBroker_settings').overrideBy('settings')
        else:
            print(__name__ + '::get_config: EXIT, cannot handle name=%s' % (name,))
            exit()
        return ans

    @staticmethod
    def choose(settingNames):
        if isinstance(settingNames, str):
            list_settingName = [settingNames]
        else:
            list_settingName = settingNames
        ans = UserConfigBase().load_settings('Config.base_settings')
        for settingName in list_settingName:
            # print(__name__ + '::choose: loading %s' % (settingFileName,))
            ans = ans.overrideBy('Config.%s' % (settingName,))
        ans = ans.overrideBy('settings')
        # print(ans)
        return ans


def test__isAllLettersCapital():
    assert(isAllLettersCapital('asdfEdasdf') is False)
    assert(isAllLettersCapital('BROKER_CLIENT') is True)
    assert(isAllLettersCapital('BROKER_CLIENt') is False)
