# coding=utf-8
import pytz
import datetime as dt

from IBridgePy.constants import TraderRunMode, MarketName

PROJECT = {
    'showTimeZone': pytz.timezone('US/Eastern'),
    'repBarFreq': 1,  # Positive numbers only
    'logLevel': 'INFO',  # Possible values are ERROR, INFO, DEBUG, NOTSET, refer to http://www.ibridgepy.com/ibridgepy-documentation/#logLevel
    'autoReconnectPremium': False,  # True: IBridgePy will automatically get reconnected to IB server when disconnect happen, such as TWW/Gateway restarts.
    'autoSearchPortNumber': True,  # True: IBridgePy will actively try to search the matched port number from searchPortList; False: IBridgePy will ONLY use settings.py -> BROKER_CLIENT -> IB_CLIENT -> port to connect.
    'searchPortList': [7496, 7497, 4001, 4002],  # Other port numbers can be added to this list if user want to use other port numbers and want to automatically search that port numbers.

    # The errors that the user wants to ignore. All IB error codes are listed here https://interactivebrokers.github.io/tws-api/message_codes.html
    # For example, the user wants to ignore this error "162	Historical market data Service error message." and "146	Invalid trigger method."
    # then, the setting can be 'errorsIgnoredByUser': [162, 146]
    # However, it is highly recommended for users to address the errors properly instead of ignoring them.
    'errorsIgnoredByUser': []
}

BACKTESTER = {
    'initPortfolioValue': 100000.0,  # The initial portfolio value when backtesting starts.
    'simulateCommission': lambda transactionShares: max(transactionShares * 0.005, 1)  # Default commission formula from Interactive Brokers is the max of either transaction shares * 0.5% or $ 1.00
}


MARKET_MANAGER = {  # these settings are applied ONLY when traderRunMode == RUN_LIKE_QUANTOPIAN
    'marketName': MarketName.NYSE,
    'beforeTradeStartHour': 9,
    'beforeTradeStartMinute': 25,
}

TRADER = {
    # Refer to https://ibridgepy.com/documentation/#runMode
    'runMode': TraderRunMode.REGULAR  # run handle_data every second. Possible values are REGULAR, RUN_LIKE_QUANTOPIAN, SUDO_RUN_LIKE_QUANTOPIAN and HFT
}

BROKER_CLIENT = {
    'IB_CLIENT': {
        'accountCode': '',
        'host': 'localhost',
        'clientId': 9,
        'port': 7496,
    },
    'TD_CLIENT': {
        'accountCode': '',
        'apiKey': '',  # put your apiKey here. Refer to this tutorial https://www.youtube.com/watch?v=l3qBYMN4yMs
        'refreshToken': '',  # put your refresh token here. Refer to this tutorial https://youtu.be/Ql6VnR0GIYY
        'refreshTokenCreatedOn': dt.date(2020, 5, 7)  # put the date when the refresh token was created. IBridgePy will remind you when it is about to expire.
    },
    'ROBINHOOD_CLIENT': {
        'accountCode': '',
        'username': '',  # put your Robinhood username here. It is ok to leave it as-is. Then, you will be prompted to input it in command line later.
        'password': '',  # put your Robinhood password here. It is ok to leave it as-is. Then, you will be prompted to input it in command line later.
    }
}

EMAIL_CLIENT = {
    'IBRIDGEPY_EMAIL_CLIENT': {
        'apiKey': ''  # To send out emails, please refer to this tutorial https://youtu.be/jkeos2QrkfQ
    }
}

