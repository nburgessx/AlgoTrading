import numpy as np
import talib as ta

def ma_crossover(data, short_lookback, long_lookback):
    data['ma_long'] = data['Close'].ewm(span=long_lookback).mean()
    data['ma_short'] = data['Close'].ewm(span=short_lookback).mean()  

    data['ma_signal'] = np.where(data.ma_short > data.ma_long, 1, 0)    
    data.iloc[:long_lookback,-1] = np.nan
    return data


def compute_adx(data, adx_threshold):
    data['adx'] = ta.ADX(data['High'], data['Low'], data['Close'], timeperiod=14)
    data['adx_signal'] = np.where(data.adx > adx_threshold, 1, 0)    
    data.iloc[:14,-1] = np.nan
    return data

