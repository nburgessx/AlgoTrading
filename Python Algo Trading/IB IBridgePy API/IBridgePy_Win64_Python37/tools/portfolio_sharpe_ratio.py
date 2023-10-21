# coding=utf-8
import pandas as pd
import matplotlib.pyplot as plt
import math
import os
import platform
import sys

# Add IBridgePy root folder to PYTHON PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime


def _plot(x):
    # Use pyplot to display strategy performance.
    plt.plot(x)
    plt.ylabel('Acct Portfolio $')
    plt.xlabel('Backtest date number')
    plt.show()


def calculate_annualized_sharpe_ratio(dailyBalance):
    """
    Calculate annualized sharpe ratio by a list of daily portfolio balances.
    Annualized Sharpe ratio assumes there are 252 trading days. = mean / std * sqrt(252)
    :param dailyBalance: a list or a pandas.Series of portfolio daily balances.
    :return: Annualized Sharpe ratio based on daily balances.
    """
    if isinstance(dailyBalance, list):
        dailyBalance = pd.Series(dailyBalance)
    f = pd.DataFrame({'close_today': dailyBalance})

    f['close_yesterday'] = dailyBalance.shift(1)  # Add a column to show close of yesterday
    f['yield'] = 0.0  # Column "yield" is daily yield: (close_today - close_yesterday)/ close_yesterday
    for index, row in f.iterrows():
        try:  # Calculate Sharpe ratio using daily returns
            f.loc[index, 'yield'] = (float(row['close_today']) - float(row['close_yesterday'])) / float(row['close_yesterday'])
        except:
            f.loc[index, 'yield'] = 0.0
    mean = f['yield'].mean()  # Simple average
    std = f['yield'].std()  # Standard deviation

    sharpe_ratio = mean / std * math.sqrt(252)
    print('annualized sharpe ratio = %s' % (sharpe_ratio,))  # Annualized Sharpe ratio assuming there are 252 trading days.
    return sharpe_ratio


def _load_file_and_draw_plot(df, columnNameOfAccountBalance):
    calculate_annualized_sharpe_ratio(df[columnNameOfAccountBalance])
    _plot(df[columnNameOfAccountBalance])


def use_sampleBalanceLog():
    # Read in the sample data and return a panda.DataFrame
    df = pd.read_csv('sampleBalanceLog.txt',
                     index_col=False,  # 1st column is NOT index
                     names=['date', 'time', 'balance', 'cash'],  # There are 4 columns in the balanceLog.txt
                     header=None,
                     delimiter=' ')
    _load_file_and_draw_plot(df, 'balance')


def use_SPY():
    # Read in the sample data and return a panda.DataFrame
    df = pd.read_csv('../Input/SPY_1day_20010103_20191214.csv', header=0)
    _load_file_and_draw_plot(df, 'Adj Close')


def use_latest_backtest_balanceLog():
    from Config.base_settings import PROJECT
    PATH = os.path.join(os.path.join(PROJECT['rootFolderPath'], 'Output'))
    fileList = os.listdir(PATH)
    ans = []
    for f in fileList:
        filePath = os.path.join(PATH, f)
        if 'BalanceLog' in filePath:
            ans.append((filePath, creation_date(filePath)))
    # print(ans)
    ans.sort(key=lambda x: x[1])
    # print(ans[-1][0])
    if not ans:
        sys.exit('There is no BalanceLog at Output folder at all. Need to run a backtest first.')
    df = pd.read_csv(ans[-1][0],
                     index_col=False,  # 1st column is NOT index
                     names=['dateTime', 'balance', 'cash'],  # There are 3 columns in the balanceLog.txt
                     header=None,
                     delimiter=' ')
    _load_file_and_draw_plot(df, 'balance')


if __name__ == '__main__':
    # use_sampleBalanceLog()
    # use_SPY()
    use_latest_backtest_balanceLog()
