# Compute daily Returns and store it in variable ret
def compute_ret(data): 
    # ret is daily returns
    data['ret'] = data['Close'].pct_change()
    data['strategy_ret'] = data.ret * data.signal.shift(1)
    return data

# Compute Sharpe Ratio and store it in variable sharpe
def rolling_sharpe(data,window):    
    import numpy as np
    data['sharpe'] = data.strategy_ret.rolling(window).mean()/data.strategy_ret.rolling(window).std()*np.sqrt(252)
    return data

# Compute rolling volatility and store it in variable volatility
def rolling_volatility(data,window):    
    data['volatility'] = data.strategy_ret.rolling(window).std()
    return data


def monthly_performance_map(data):
    data["Year"] = data.index.map(lambda x: x.year)
    data["Month"] = data.index.map(lambda x: x.strftime("%b"))
    pt = data.pivot_table(index="Month",columns="Year",values="strategy_ret", aggfunc="sum").fillna(0)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    pt = pt.reindex(months)    
    import seaborn as sns
    sns.heatmap(pt, annot=True, cmap="RdYlGn")