# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 23:50:16 2018

@author: IBridgePy@gmail.com
"""

from IBridgePy.constants import DataProviderName
from tools.hist_converter import get_hist_from_csv
from .data_provider_nonRandom import NonRandom


class LocalFile(NonRandom):
    @property
    def name(self):
        return DataProviderName.LOCAL_FILE

    def provide_hist_from_a_true_dataProvider(self, security, endTime, goBack, barSize, whatToShow, useRTH):
        # Need to think about how to use this method
        raise NotImplementedError(self.name)

    def provide_real_time_price(self, security, tickType):
        # Need to think about how to use this method
        raise NotImplementedError(self.name)

    def ingest_hists(self, histIngestionPlan):
        """
        csv file must have 1st column integer as epoch, then open high low close volume
        hist index must be integer representing epoch time in seconds
        because it will be easier to server data when searching a spot time
        :param histIngestionPlan: histIngestionPlan: data_provider_factor::data_loading_plan::HistIngestionPlan
        :return:
        """
        self._ingest_hists(histIngestionPlan, self._get_hist_from_csv)
        self._histIngested = True

    def _get_hist_from_csv(self, plan):
        return get_hist_from_csv(plan.fullFileName, self._log)
