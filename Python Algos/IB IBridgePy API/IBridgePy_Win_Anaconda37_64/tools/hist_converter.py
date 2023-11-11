# coding=utf-8
import pytz
import sys
import os

# Add IBridgePy root folder to PYTHON PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BasicPyLib.BasicTools import timestamp_to_epoch, epoch_to_dt, dt_to_epoch, date_to_epoch
import numpy as np
import pandas as pd
import datetime as dt
from sys import exit


def convert_hist_using_datetime_to_epoch(hist):
    if isinstance(hist.index[-1], dt.datetime):
        hist['epoch'] = hist.index.map(dt_to_epoch)
    elif isinstance(hist.index[-1], dt.date):
        hist['epoch'] = hist.index.map(date_to_epoch)
    else:
        exit(__name__ + '::convert_hist_using_datetime_to_epoch: EXIT, cannot handle hist.index type=%s' % (type(hist.index[-1]),))
    hist = hist.reset_index()
    hist = hist.set_index('epoch')
    # assert(isinstance(hist.index[-1], np.int64))
    return hist


def convert_hist_using_timestamp_to_epoch(hist):
    hist['epoch'] = hist.index.map(timestamp_to_epoch)
    hist = hist.reset_index()
    hist = hist.set_index('epoch')
    assert(isinstance(hist.index[-1], np.int64))
    return hist


def convert_hist_using_epoch_to_timestamp(hist, to_timezone=pytz.utc):
    hist['timestamp'] = hist.index.map(epoch_to_dt)  # When datetime is used as pd.index, its format is pd.Timestamp, not datetime anymore.
    hist = hist.reset_index()
    hist = hist.set_index('timestamp')
    hist.drop('index', axis=1)
    hist.index = hist.index.tz_convert(to_timezone)
    return hist


def get_hist_from_csv(full_path, log=None):
    # print(__name__ + f'::get_hist_from_csv: full_path={full_path}')
    hist = pd.read_csv(full_path,
                       index_col=0,  # first column is index column
                       # parse_dates=True,  # first column should be parse to date
                       # date_parser=epoch_to_dt,  # this is the parse function
                       header=0)  # first row is header row
    # If the index is int64, that is good enough, no need to convert.
    if isinstance(hist.index[-1], np.int64):
        if log:
            log.info('Ingested hist from filePath=%s' % (full_path,))
        hist.rename(columns=lambda x: x.lower(), inplace=True)
        return hist
    else:  # if index is string, needs to convert index from string to epoch second
        hist = pd.read_csv(full_path,
                           index_col=0,  # first column is index column
                           parse_dates=True,  # first column should be parsed to pd.Timestamp
                           header=0)  # first row is header row
        if log:
            log.info('Ingested hist from filePath=%s' % (full_path,))
        hist.rename(columns=lambda x: x.lower(), inplace=True)
        return convert_hist_using_timestamp_to_epoch(hist)
