# coding=utf-8
import datetime as dt

from IBridgePy.IbridgepyTools import symbol
from configuration import test_me
from data_provider_factory.data_loading_plan import HistIngestionPlan, Plan

# Related YouTube tutorials about IBridgePy backtester
# Build “Buy low Sell high” strategy by Machine learning https://youtu.be/hNCwNxeXrwA
# Detailed explanation about “Buy low Sell high” strategy https://youtu.be/PI5dhqCAuvA
# Calculate Sharpe Ratio https://youtu.be/4xTHdzAMhcI
# Backtest without hist ingestion https://youtu.be/bwmx5hiSPV4
# Backtest with hist ingestion https://youtu.be/XnpxAVU4ogY
# Backtest with hist from local files https://youtu.be/UR_7_F8wPL0
# Speed up backtest by designating spot times https://youtu.be/bVE59nZ02ig
# Convert hist data format https://youtu.be/hYL6SYgy7wE
# Backtest using IBridgePy data center https://youtu.be/0FPgtmUpTI0
fileName = 'demo_buy_low_sell_high.py'

accountCode = 'DU1868499'  # IB accountCode is needed to retrieve historical data from IB server.
dataProviderName = 'IB'  # RANDOM, IB, LOCAL_FILE, TD, ROBINHOOD, IBRIDGEPY

####
# The backtesting time period is defined by two variables: endTime and startTime, default timezone = 'US/Eastern'
####

# As a demo, endTime is the current time.
# IBridgePy automatically sets endTime.second to 0 because the default mode of IBridgePy backtester is designed to
# backtest strategies minutely and the second must be zero.
endTime = dt.datetime.now()

# As a demo, startTime is 50 days ago from the current time.
startTime = endTime - dt.timedelta(days=50)

# "histIngestionPlan" is a reserved word in IBridgePy to store the historical data ingestion plan that describes what historical data
# are needed during backtesting and IBridgePy backtester will fetch these data before backtesting to speed up the whole backtesting process.
# "histIngestionPlan" is not required for backtesting but it will make backtest much faster.
# "histIngestionPlan" is an instance of HistIngestionPlan.
histIngestionPlan = HistIngestionPlan()
histIngestionPlan.add(Plan(security=symbol('SPY'), barSize='1 min', goBack='40 D'))  # "histIngestionPlan.add" is used to add more Ingestion Plans
histIngestionPlan.add(Plan(security=symbol('SPY'), barSize='1 day', goBack='55 D'))  # "histIngestionPlan.add" is used to add more Ingestion Plans

test_me(fileName, globals())
