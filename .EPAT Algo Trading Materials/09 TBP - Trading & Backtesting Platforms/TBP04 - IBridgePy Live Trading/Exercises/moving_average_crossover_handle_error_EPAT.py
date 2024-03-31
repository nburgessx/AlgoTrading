# -*- coding: utf-8 -*-

"""
There is a risk of loss when trading stocks, futures, forex, options and other
financial instruments. Please trade with capital you can afford to
lose. Past performance is not necessarily indicative of future results.
Nothing in this computer program/code is intended to be a recommendation, explicitly or implicitly, and/or
solicitation to buy or sell any stocks or futures or options or any securities/financial instruments.
All information and computer programs provided here is for education and
entertainment purpose only; accuracy and thoroughness cannot be guaranteed.
Readers/users are solely responsible for how to use these information and
are solely responsible any consequences of using these information.

If you have any questions, please send email to IBridgePy@gmail.com
All rights reserved.
"""


def initialize(context):
    context.run_once = False  # To show if the handle_data has been run in a day
    context.security = symbol('SPY')  # Define a security for the following part

    # a variable to flag if today is early close.
    # Regular close at 16:00 Eastern time.
    # Eearly close at 13:00 Eastern time.
    context.isTodayEarlyClose = False

    # isEarlyClose() is an expensive function. Only check once at 10:00AM every day
    schedule_function(check_early_close, date_rule=date_rules.every_day(),
                      time_rule=time_rules.spot_time(hour=10, minute=0))

    # Send out email about account balance every day after market is closed.
    schedule_function(send_email_scheduleable, date_rule=date_rules.every_day(),
                      time_rule=time_rules.spot_time(hour=16, minute=30))

def check_early_close(context, data):
    """
    isEarlyClose() is an expensive function. Only check once at 10:00AM every day.
    Then, save the result to context.isTodayEarlyClose
    """
    context.isTodayEarlyClose = isEarlyClose()
    context.run_once = False  # reset the flag to trade


def send_email_scheduleable(context, data):
    if not isTradingDay():
        send_email(emailTitle='Not a trading day', emailBody='Not a trading day', toEmail='youremail@domain.com')
    else:
        acctBalance = show_account_info('NetLiquidation')
        send_email(emailTitle='Account balance today', emailBody=str(acctBalance), toEmail='uva.liu.hui@gmail.com')


# Refer to this Wiki page about Moving average crossover strategy
# https://en.wikipedia.org/wiki/Moving_average_crossover
def handle_data(context, data):

    # If today is not a trading day, just do not continue
    if not isTradingDay():
        return

    if context.isTodayEarlyClose:
        handle_early_close(context, data)
    else:
        handle_regular_close(context, data)


def handle_early_close(context, data):
    sTime = get_datetime('US/Eastern')
    if sTime.hour == 12 and sTime.minute == 59 and context.run_once is False:
        make_trade_decision(context, data)


def handle_regular_close(context, data):
    sTime = get_datetime('US/Eastern')
    if sTime.hour == 15 and sTime.minute == 59 and context.run_once is False:
        make_trade_decision(context, data)


def make_trade_decision(context, data):
    # 1 minute before the market closes, do moving average calculation
    # if MA(5) > MA(60), then BUY the security if there is no order
    # Keep the long positions if there is a long position
    # if MA(5) < MA(60), clear the position
    hist = data.history(context.security, 'close', 80, '1d')  # fetch enough historical data to calculate Moving Average
    mv_5 = hist.rolling(5).mean()[-1]  # the latest fast moving average value
    mv_60 = hist.rolling(60).mean()[-1]  # the latest slow moving average value
    if mv_5 > mv_60:
        try:
            orderId = order_target_percent(context.security, 1.0)  # Place 100% of portfolio buy SPY
            order_status_monitor(orderId, target_status='Filled')
        except RuntimeError as e:
            send_email(emailTitle='Something is wrong today', emailBody=str(e), toEmail='youremail@gmail.com')
    else:
        try:
            orderId = order_target_percent(context.security, 0.0)  # Sell off all positions in my account
            order_status_monitor(orderId, target_status='Filled')
        except RuntimeError as e:
            send_email(emailTitle='Something is wrong today', emailBody=str(e), toEmail='youremail@gmail.com')
    context.run_once = True
