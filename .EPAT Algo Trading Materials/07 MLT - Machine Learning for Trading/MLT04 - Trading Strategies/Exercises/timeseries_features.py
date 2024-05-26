import numpy as np
import pandas as pd
from scipy.signal import resample
from scipy.spatial import Delaunay
import numba as nb


def permutation_entropy(timeseries, m):
    """
    This implementation takes as input a time series timeseries and the parameter m,
    which represents the length of the subsequences used to compute the permutation entropy.
    The function first constructs a permutations array,
    which stores the count of each unique permutation of the subsequence of length m in the time series.
    The entropy is then computed using the permutations array and returned as the result.

    :param timeseries:
    :param m:
    :return:
    """
    n = len(timeseries)
    permutations = np.zeros((m, m))
    for i in range(n - m + 1):
        subsequence = np.array(timeseries[i : i + m])
        rank = np.argsort(subsequence).argsort()
        permutations[rank, np.roll(rank, -1)] += 1

    permutations = permutations / (n - m + 1)
    permutations = permutations[np.nonzero(permutations)]
    entropy = -np.sum(permutations * np.log(permutations)) / np.log(m)

    return entropy


@nb.njit
def hurst(ts):
    n = len(ts)
    R = np.zeros(n)
    for i in range(n):
        R[i] = np.max(ts[: i + 1]) - np.min(ts[: i + 1])
    R = np.mean(R)
    lags = np.arange(2, n // 3)
    tau = np.asarray(
        [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    )
    X = np.log(lags).reshape(-1, 1)
    Y = np.log(tau).reshape(-1, 1)
    coefficients, _, _, _ = np.linalg.lstsq(X, Y)
    return coefficients[0] * 2.0


@nb.njit
def box_counting(ts, box_size):
    N = len(ts)
    boxes = np.zeros(N // box_size)
    for i in range(0, N, box_size):
        boxes[i // box_size] = np.max(ts[i : i + box_size]) - np.min(
            ts[i : i + box_size]
        )
    return np.count_nonzero(boxes > 0)


@nb.njit
def fractal_dimension(ts, n_box_sizes=10):
    N = len(ts)
    box_sizes = np.logspace(0, np.log10(N), n_box_sizes).astype(np.int32)
    box_counts = np.array([box_counting(ts, bs) for bs in box_sizes])
    log_box_sizes = np.log(box_sizes)
    log_counts = np.log(box_counts)
    log_box_sizes = log_box_sizes.reshape(-1, 1)
    log_counts = log_counts.reshape(-1, 1)
    coef, _, _, _ = np.linalg.lstsq(log_box_sizes, log_counts, rcond=None)
    return -coef[0][0]


def roll_measure(close_prices, window):
    close_prices = pd.Series(close_prices)
    log_returns = np.log(close_prices).diff().dropna()
    cum_returns = log_returns.cumsum()
    rolled_returns = cum_returns.rolling(window).apply(lambda x: x[-1] - x[0])
    return rolled_returns


def corwin_schultz_hl(high, low, volume, window):
    spread = high - low
    spread_return = np.log(spread / spread.shift(1))
    volume_weighted_spread_return = (
        spread_return * volume / volume.rolling(window).sum()
    )
    rolling_average_spread_return = volume_weighted_spread_return.rolling(window).mean()
    corwin_schultz_estimator = np.exp(rolling_average_spread_return.cumsum()) - 1
    return corwin_schultz_estimator


def bekker_parkinson_vol(high_prices, low_prices, close_prices, window=10):
    mid_prices = (high_prices + low_prices) / 2
    log_returns = np.log(mid_prices / close_prices.shift(1))
    rqv = np.cumsum(log_returns**2)
    bp_vol = np.sqrt(rqv / window)
    return bp_vol


def kyles_lambda(close, volume, window):
    mid = (close + close.shift(1)) / 2
    lambda_ = (
        np.abs(volume * (close - mid))
        / (volume * (mid - close.shift(1))).rolling(window=2).sum()
    )
    rolling_lambda = lambda_.rolling(window=window).mean()
    return rolling_lambda


def amihuds_lambda(close_prices, trade_volumes, window=10):
    log_returns = np.log(close_prices / close_prices.shift(1))
    daily_illiquidity = np.abs(trade_volumes) / (close_prices * trade_volumes.sum())
    lambdas = np.abs(log_returns) / daily_illiquidity
    return pd.Series(lambdas, index=close_prices.index).rolling(window).mean()


def hasbroucks_lambda(close_prices, trade_volumes, window=10):
    log_returns = np.log(close_prices / close_prices.shift(1))
    mean_abs_return = np.abs(log_returns).rolling(window).mean()
    mean_abs_trade_size = np.abs(trade_volumes).rolling(window).mean()
    lambdas = mean_abs_return / mean_abs_trade_size
    return pd.Series(lambdas, index=close_prices.index).rolling(window).mean()
