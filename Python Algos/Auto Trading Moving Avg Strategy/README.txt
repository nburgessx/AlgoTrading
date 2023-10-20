Implementation Guide - Auto Trading Moving Average Strategy
===========================================================

1. Excel Prototype - Trading Moving Avg.xlsx
============================================
First, we prototype a simple and exponential moving average trading strategy.
We optimize for the best moving average parameters using Excel's "what-if" solver.
Furthermore we generate trading strategy performance metrics and compute the
sharpe ratio and Kelly Criterion for money management purposes.

2. Python Prototype - TradingMovingAvg.ipynb
============================================
Second, using a Jupyter notebook and interactive python we prototype the strategy
in Python with extensive visualization and performance analytics on show.

3. Automated Trading Strategy - AutoTradingMA.ipynb
===================================================
Third, we show how to automate the trading strategy in Python using a vectorized
approach for good performance. This allows us to analyize a wide range of data 
and securities quickly. The Python code sources market data from yahoo finance
and automatically backtests the strategy on a portfolio of tech stocks and searches
for best performing underlying. We also optimize for the best model parameters
and produce extensive trading strategy performance metrics.

4. Automated Trading Strategy using Tick Data - AutoTradingMA-TickDataVersion.ipynb
===================================================================================
Fourth, we extend the Python automated trading strategy using an event driven approach,
which allows us to work with tick data. This makes it simpler to add stop-losses and
easier to work with real-time and live streaming data. In the Python notebook, we
source data again from yahoo finance and implement an order management class to place
trades and track account balances and incrental performance. We implement the trading
strategy utilizing the data streaming and order management class, and demo how to manage
trades with tick data and how to add stop losses to the strategy.

These are demo files to give an overview of the basic features of an automated trading
strategy. These ideas can easily be expanded upon to create a live trading strategy.

Have fun! Bye Bye! 

