# coding=utf-8
import bisect
import datetime as dt
import os
from sys import exit

import pandas as pd
import pytz

from BasicPyLib.BasicTools import dt_to_epoch, epoch_to_dt
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.IbridgepyTools import stripe_exchange_primaryExchange_from_security, adjust_endTime, \
    convert_goBack_barSize
from IBridgePy.constants import DataProviderName, DataSourceName
from broker_client_factory.CustomErrors import NotEnoughHist
from .data_provider import DataProvider


def _convert_strDatetime_to_epoch_int(aDatetime):
    # !!!!strptime silently discard tzinfo!!!
    aDatetime = dt.datetime.strptime(aDatetime, "%Y%m%d %H:%M:%S %Z")  # string -> dt.datetime
    aDatetime = pytz.timezone('UTC').localize(aDatetime)
    return int(dt_to_epoch(aDatetime))


def _search_index_location_in_hist(hist, aDatetime):
    intDatetime = int(dt_to_epoch(aDatetime))
    if intDatetime not in hist.index:
        indexPosition = bisect.bisect_left(hist.index, intDatetime)
        if indexPosition >= len(hist.index):
            indexPosition -= 1
        ans = indexPosition
        # print(__name__ + f'::_search_index_location_in_hist: {aDatetime}={intDatetime} not in hist ans={ans}')
        return ans
    else:
        ans = hist.index.get_loc(intDatetime)
        # print(__name__ + '::_search_index_location_in_hist: ans=%s' % (ans,))
        return ans


# !!! Everything will ONLY be used for backtester.!!!
class NonRandom(DataProvider):
    def __init__(self, userConfig, log, useColumnNameWhenSimulatedByDailyBar):
        self._1minHist = {}

        # used to record with histIngestionPlan is simulatedByDailyBar. the value is tuple(str_security, freq)
        self._simulatedByDailyBars = set()
        super().__init__(userConfig, log, useColumnNameWhenSimulatedByDailyBar)

    def provide_hist_from_a_true_dataProvider(self, security, endTime, goBack, barSize, whatToShow, useRTH):
        raise NotImplementedError(self.name)

    def provide_real_time_price(self, security, tickType):
        raise NotImplementedError(self.name)

    def ingest_hists(self, histIngestionPlan):
        # histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        raise NotImplementedError(self.name)

    def _ingest_hists(self, histIngestionPlan, funcToFetchHist):
        """
        Read in ingestion plan and use funcToFetchHist to fetch hist and Then, save them to self._hist.
        :param histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        :param funcToFetchHist: the passed in function is responsible to convert the format to the required format
        :return: None
        """
        self._log.debug(__name__ + '::_ingest_hists: loadingPlan=%s client=%s' % (histIngestionPlan, self._dataProviderClient))
        if not histIngestionPlan:
            return
        for plan in histIngestionPlan.finalPlan:
            security_no_exchange_primaryExchange = stripe_exchange_primaryExchange_from_security(plan.security)
            str_security_no_exchange_primaryExchange = security_no_exchange_primaryExchange.full_print()
            barSize = plan.barSize.lower()
            if str_security_no_exchange_primaryExchange not in self._hist:
                self._hist[str_security_no_exchange_primaryExchange] = {}
            if barSize not in self._hist[str_security_no_exchange_primaryExchange]:
                self._hist[str_security_no_exchange_primaryExchange][barSize] = {}
            if plan.dataSourceName == DataSourceName.SIMULATED_BY_DAILY_BARS:
                self._simulatedByDailyBars.add((str_security_no_exchange_primaryExchange, barSize))
                continue
            df_hist = funcToFetchHist(plan)
            if not len(df_hist):
                raise NotEnoughHist()
            self._hist[str_security_no_exchange_primaryExchange][barSize] = df_hist
            if histIngestionPlan.saveToFile:
                PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                targetDir = os.path.join(PROJECT_ROOT_DIR, 'Input')
                if not os.path.exists(targetDir):
                    os.mkdir(targetDir)
                targetFileFullName = os.path.join(targetDir, '%s_%s_%s.csv' % (plan.security, plan.barSize, plan.goBack))
                if os.path.exists(targetFileFullName):
                    self._log.info('%s exists !!! Please delete it or rename it and try backtest again!' % (targetFileFullName,))
                    exit()
                df_hist.to_csv(targetFileFullName)
                self._log.info('Saved hist to %s' % (targetFileFullName,))
            self._log.info('ingested hist of security=%s barSize=%s from %s' % (str_security_no_exchange_primaryExchange, barSize, self.name))
            try:
                firstLineDatetime = epoch_to_dt(self._hist[str_security_no_exchange_primaryExchange][barSize].index[0], str_timezone='US/Eastern')
                lastLineDatetime = epoch_to_dt(self._hist[str_security_no_exchange_primaryExchange][barSize].index[-1], str_timezone='US/Eastern')
                if firstLineDatetime >= lastLineDatetime:
                    # self._log.error('The timestamp of the 1st line=%s and the timestamp of the last line=%s. EXIT: The timestamp of the 1st line must be earlier than the timestamp of the last line!' % (firstLineDatetime, lastLineDatetime))
                    self._hist[str_security_no_exchange_primaryExchange][barSize] = self._hist[str_security_no_exchange_primaryExchange][barSize].sort_index()
                    firstLineDatetime = epoch_to_dt(self._hist[str_security_no_exchange_primaryExchange][barSize].index[0], str_timezone='US/Eastern')
                    lastLineDatetime = epoch_to_dt(self._hist[str_security_no_exchange_primaryExchange][barSize].index[-1], str_timezone='US/Eastern')
                self._log.info('1st line=%s' % (firstLineDatetime,))
                self._log.info('last line=%s' % (lastLineDatetime,))
            except ValueError:
                self._log.error('security=%s barSize=%s index=%s is not valid. The format of index should be epoch time. Refer to https://www.epochconverter.com/' % (str_security_no_exchange_primaryExchange, barSize, self._hist[str_security_no_exchange_primaryExchange][barSize].index[0]))
                self._log.error('If you need help on coding, please refer to the well known Rent-a-Coder service https://ibridgepy.com/rent-a-coder/')
                exit()
        # if len(self._hist) == 0:
        #    self._log.debug(__name__ + '::ingest_hists: EXIT, loading errors')
        #    exit()

    @property
    def name(self):
        return 'NonRandom'

    def _get_one_real_time_price_from_local_variable_hist(self, security, timeNow, tickType):
        """
        Both of prices and volume will be provided.
        :param security:
        :param timeNow:
        :param tickType: string ONLY
        :return:
        """
        # print(__name__, '_get_one_real_time_price_from_local_variable_hist', security, timeNow, tickType)
        if not self._histIngested:
            self._log.error(__name__ + '::_get_one_real_time_price_from_local_variable_hist: EXIT, hist has not been ingested.')
            exit()
        fieldName = None
        if tickType in [IBCpp.TickType.ASK, IBCpp.TickType.BID, IBCpp.TickType.LAST, IBCpp.TickType.OPEN]:
            fieldName = 'open'
        elif tickType == IBCpp.TickType.HIGH:
            fieldName = 'high'
        elif tickType == IBCpp.TickType.LOW:
            fieldName = 'low'
        elif tickType == IBCpp.TickType.CLOSE:
            fieldName = 'close'
        elif tickType == IBCpp.TickType.VOLUME:
            fieldName = 'volume'
        else:
            self._log.error(__name__ + '::_get_one_real_time_price_from_local_variable_hist: EXIT, cannot handle tickType=%s' % (tickType,))
            exit()

        security_no_exchange_primaryExchange = stripe_exchange_primaryExchange_from_security(security)
        str_security = security_no_exchange_primaryExchange.full_print()

        # IB only accepts str_endTime with a timezone of UTC.
        timeNow = timeNow.astimezone(pytz.utc)

        # If 1 minute bar is labeled as simulatedByDailyBars, it means to get daily bar that contains the timeNow and then,
        # use "close" price of the daily bar to simulate minute price.
        if (str_security, '1 min') in self._simulatedByDailyBars:
            int_timeNow = int(dt_to_epoch(timeNow))
            hist = self._hist[str_security]['1 day']
            if int_timeNow in hist.index:
                ans = hist.loc[int_timeNow, self._useColumnNameWhenSimulatedByDailyBar]
                self._log.notset(__name__ + '::_get_one_real_time_price_from_local_variable_hist: simulatedByDailyBars str_security=%s timeNow=%s tickType=%s returnedValue=%s' % (str_security, int_timeNow, tickType, ans))
                return ans
            else:
                # bisect_left is to find the loc and insert a row on the left of the loc.
                # Therefore, "-1" is needed to find the correct daily bar
                # for example, timeNow = 2020-12-23 15:59:00 -0500, then, timeNowPosition should be 2020-12-23
                timeNowPosition = bisect.bisect_left(hist.index, int_timeNow) - 1
                if timeNowPosition >= len(hist.index):
                    timeNowPosition -= 1
                ans = hist.iloc[timeNowPosition][self._useColumnNameWhenSimulatedByDailyBar]
                self._log.debug(__name__ + '::_get_one_real_time_price_from_local_variable_hist: simulatedByDailyBars str_security=%s timeNow=%s tickType=%s returnedValue=%s' % (str_security, int_timeNow, tickType, ans))
                return ans
        if str_security not in self._hist:
            str_timeNow = dt.datetime.strftime(timeNow, "%Y%m%d %H:%M:%S %Z")  # datetime -> string
            if (security, str_timeNow) in self._1minHist:
                return self._1minHist[(security, str_timeNow)].iloc[-1][fieldName]
            if self.name in [DataProviderName.IB, DataProviderName.ROBINHOOD, DataProviderName.ROBINHOOD, DataProviderName.IBRIDGEPY]:
                self._log.info('Do not have hist for str_security=%s' % (str_security,))
                if security.secType != 'CASH':
                    return self._helper(security, str_timeNow, fieldName)
                else:
                    return self._helper(security, str_timeNow, fieldName, 'ASK')
            else:
                self._log.error(__name__ + '::_get_one_real_time_price_from_local_variable_hist: EXIT, not enough hist %s, %s from dataProviderName=%s' % (security, str_timeNow, self.name,))
                raise NotEnoughHist()

        # If hist of 1 sec is provided for backtesting, it is used for real time price. Otherwise, use 1 min bar for real time price.
        if '1 sec' in self._hist[str_security]:
            freq = '1 sec'
        else:
            freq = '1 min'

        if freq not in self._hist[str_security]:
            str_timeNow = dt.datetime.strftime(timeNow, "%Y%m%d %H:%M:%S %Z")  # datetime -> string
            if (security, str_timeNow) in self._1minHist:
                return self._1minHist[(security, str_timeNow)].iloc[-1][fieldName]
            self._log.info(__name__ + '::_get_one_real_time_price_from_local_variable_hist: hist of %s does not have freq=%s' % (str_security, freq))
            if security.secType != 'CASH':
                return self._helper(security, str_timeNow, fieldName)
            else:
                return self._helper(security, str_timeNow, fieldName, 'ASK')

        int_timeNow = int(dt_to_epoch(timeNow))
        hist = self._hist[str_security][freq]
        if int_timeNow in hist.index:
            ans = hist.loc[int_timeNow, fieldName]
            self._log.debug(__name__ + '::_get_one_real_time_price_from_local_variable_hist: str_security=%s timeNow=%s tickType=%s returnedValue=%s' % (str_security, int_timeNow, tickType, ans))
            return ans
        else:
            # Solution: if timeNow is not in hist, then raise Exception. Maybe it is not a good idea
            # timeNow = epoch_to_dt(timeNow).astimezone(self.showTimeZone)  # default is UTC
            # time1st = epoch_to_dt(self.hist[str_security][freq].index[0]).astimezone(self.showTimeZone)
            # timeLast = epoch_to_dt(self.hist[str_security][freq].index[-1]).astimezone(self.showTimeZone)
            # self._log.error(__name__ + '::get_one_real_time_prices: loaded hist does not have timeNow=%s' % (str(timeNow),))
            # self._log.error(__name__ + '::get_one_real_time_prices: loaded hist of security=%s from %s to %s'
            #                % (str_security,  time1st, timeLast))
            # raise AssertionError  # AssertionError will be caught by broker_client_factory::BrokerClient_Local.py::processMessagesWrapper

            # Solution 2: look for the timeBar immediately before timeNow, and use its value.
            timeNowPosition = bisect.bisect_left(hist.index, int_timeNow)
            if timeNowPosition >= len(hist.index):
                timeNowPosition -= 1
            ans = hist.iloc[timeNowPosition][fieldName]
            self._log.debug(__name__ + '::_get_one_real_time_price_from_local_variable_hist: str_security=%s timeNow=%s tickType=%s returnedValue=%s' % (str_security, int_timeNow, tickType, ans))
            return ans

    def _helper(self, security, str_timeNow, fieldName, priceType='TRADES'):
        self._log.info('IBridgePy has to request 1 min bar at %s from a broker %s to continue backtesting but it will be slow. Recommend to add HistIngestPlan in TEST_ME.py' % (str_timeNow, self.name))
        hist = self.provide_hist_from_a_true_dataProvider(security, str_timeNow, '60 S', '1 min', priceType, useRTH=1)
        self._1minHist[(security, str_timeNow)] = hist
        return hist.iloc[-1][fieldName]

    # !!! the returned hist will only be used for backtester.!!!
    def provide_historical_data_from_local_variable_hist(self, security, endTime, goBack, barSize, whatToShow, useRTH):
        """

        :param security: IBridgePy::quantopian::Security
        :param endTime: request's ending time with format yyyyMMdd HH:mm:ss {TMZ} ---from IB api doc
        :param goBack: 'x S' 'x D' 'x W' 'x M' 'x Y'
        :param barSize: string 1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins,
                                30 mins, 1 hour, 1 day
        :param whatToShow:
        :param useRTH:
        :return:
        """
        self._log.debug(__name__ + '::provide_historical_data_from_local_variable_hist: endTime=%s goBack=%s barSize=%s' % (endTime, goBack, barSize))
        if not self._histIngested:
            self._log.error(__name__ + '::provide_historical_data_from_local_variable_hist: EXIT, hist has not been ingested.')
            exit()

        # Read in self.hist to provide data and check errors
        security_no_exchange_primaryExchange = stripe_exchange_primaryExchange_from_security(security)
        securityFullPrint = security_no_exchange_primaryExchange.full_print()
        barSize = barSize.lower()
        if securityFullPrint not in self._hist:
            self._log.debug(__name__ + '::provide_historical_data_from_local_variable_hist: hist of %s is not ingested.' % (securityFullPrint,))
            raise NotEnoughHist()
        if barSize not in self._hist[securityFullPrint]:
            self._log.info(__name__ + '::provide_historical_data_from_local_variable_hist: hist of %s exists but barSize=%s is not ingested.' % (securityFullPrint, barSize))
            raise NotEnoughHist()
        hist = self._hist[securityFullPrint][barSize]
        if not isinstance(hist, pd.DataFrame):
            self._log.debug(__name__ + '::provide_historical_data_from_local_variable_hist: hist is empty')
            raise NotEnoughHist()

        endTime = adjust_endTime(endTime, barSize)
        endTimePosition = _search_index_location_in_hist(hist, endTime)
        startTimePosition = endTimePosition - convert_goBack_barSize(goBack, barSize)
        if startTimePosition >= len(hist) - 2 or startTimePosition < 0:
            self._error_message(hist, securityFullPrint, barSize, endTime)
            raise NotEnoughHist()

        if startTimePosition < endTimePosition:
            # print(f'startTimePosition={startTimePosition} endTimePosition={endTimePosition}')
            return hist.iloc[startTimePosition:endTimePosition + 1]
        else:
            self._error_message(hist, securityFullPrint, barSize, endTime)
            raise NotEnoughHist()

    def _error_message(self, hist, securityFullPrint, barSize, endTime):
        dt_firstLine = epoch_to_dt(hist.index[0])
        dt_lastLine = epoch_to_dt(hist.index[-1])
        self._log.info(f'EXIT, Not enough hist security={securityFullPrint} barSize={barSize} is provided to backtest.')
        self._log.info(f'First line in hist={dt_firstLine}')
        self._log.info(f'Last line in hist={dt_lastLine}')
        if endTime < epoch_to_dt(hist.index[0]):
            self._log.info(f'Backtest at this spot time={endTime} is earlier than first line={dt_firstLine}')
        elif endTime > epoch_to_dt(hist.index[-1]):
            self._log.info(f'Backtest at this spot time={endTime} is later than last line={dt_lastLine}')
