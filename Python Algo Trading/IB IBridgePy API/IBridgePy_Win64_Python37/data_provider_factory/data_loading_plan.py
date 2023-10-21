# coding=utf-8
import datetime as dt
import os

import pytz

from BasicPyLib.Printable import PrintableII
from broker_client_factory.BrokerClientDefs import ReqHistParam


class Plan(PrintableII):
    """
    Each SecurityHistLoadingPlan contains the loading __init__ of each security
    """
    def __init__(self, security=None, barSize=None, goBack=None,
                 endTime=None, dataSourceName=None, fileName=None, folderName=None):
        """

        :param security: Must be IBridgePy::quantopian::Security, because it is friendly to users.
        """
        self.security = security
        self.barSize = barSize
        self.goBack = goBack
        self.endTime = endTime
        self.dataSourceName = dataSourceName
        self.fileName = fileName
        self.folderName = folderName
        self.fullFileName = None
        if self.folderName is not None and self.fileName is not None:
            self.fullFileName = os.path.join(self.folderName, self.fileName)


class HistIngestionPlan(PrintableII):
    """
    finalPlan is a Set() to contain all specific plans
    """
    def __init__(self, defaultBarSize=ReqHistParam.BarSize.ONE_MIN,
                 defaultGoBack=ReqHistParam.GoBack.ONE_DAY,
                 defaultEndTime=pytz.timezone('US/Pacific').localize(dt.datetime.now()),
                 defaultDataSourceName=None,
                 defaultFolderName=None,
                 saveToFile=False):
        """

        :param defaultBarSize:
        :param defaultGoBack:
        :param defaultEndTime:
        :param defaultDataSourceName:
        :param defaultFolderName:
        :param saveToFile: bool if save the retried hist data to file for loading from file to backtest later.
        """

        self.barSize = defaultBarSize
        self.goBack = defaultGoBack
        self.endTime = defaultEndTime
        self.dataSourceName = defaultDataSourceName
        if not defaultFolderName:
            self.folderName = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Input')
        else:
            self.folderName = defaultFolderName
        self.finalPlan = set()
        self.saveToFile = saveToFile

    def add(self, plan):
        # If singlePlan does not specify param, just use default values in LoadingPlan
        for ct in ['barSize', 'goBack', 'endTime', 'dataSourceName', 'folderName']:
            if getattr(plan, ct) is None:
                setattr(plan, ct, getattr(self, ct))

        # Add folderName in front of fileName to make a full fileName
        if plan.fileName is not None:
            plan.fullFileName = os.path.join(plan.folderName, plan.fileName)
        self.finalPlan.add(plan)
        return self

    def getFinalPlan(self):
        return self.finalPlan
