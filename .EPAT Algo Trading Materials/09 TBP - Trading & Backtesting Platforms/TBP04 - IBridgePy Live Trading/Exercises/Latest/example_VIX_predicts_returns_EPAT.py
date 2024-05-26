# -*- coding: utf-8 -*-
'''
There is a risk of loss in stocks, futures, forex and options trading. Please
trade with capital you can afford to lose. Past performance is not necessarily
indicative of future results. Nothing in this computer program/code is intended
to be a recommendation to buy or sell any stocks or futures or options or any
tradable securities.
All information and computer programs provided is for education and
entertainment purpose only; accuracy and thoroughness cannot be guaranteed.
Readers/users are solely responsible for how they use the information and for
their results.

If you have any questions, please send email to IBridgePy@gmail.com
'''

'''
VIX predicts returns

Strategy
The investor uses the rolling past 20 year history of the VIX index to create 20
equally spaced percentiles. He/she then goes long on the equity index at the 
close for one day if the VIX index on the current day is higher than on any 
other day during the rolling 2 year window or if the VIX index value is in the 
highest 2 percentile boxes. He/she goes short on the equity index at the close 
for one day if the VIX index on the current day is lower than on any other day 
during the rolling 2 year window or if the VIX index value is in the lowest 2 
percentile boxes.
Source Paper
Giot: On the relationships between implied volatility indices and stock index returns
http://www.core.ucl.ac.be/econometrics/Giot/Papers/IMPLIED2_i.pdf
http://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=5ABA12147DEB71866EF16F4D51343C90?doi=10.1.1.199.4665&rep=rep1&type=pdf
Abstract:
For the S&P100 and NASDAQ100 indices, we show that there is a negative and 
statistically significant relationship between the returns of the stock and 
implied volatility (VIX and VXN) indices. For the S&P100 index, this 
relationship is asymmetric as negative stock index returns yield bigger changes 
in VIX than do positive returns. The VIX’s response to negative stock index 
returns is sharper in low-volatility periods, which suggests that option 
traders react aggressively to negative returns in low-volatility periods by 
strongly bidding up implied volatility. For the NASDAQ100 index, the asymmetric 
effect is rather weak but the VXN response to the index is also somewhat muted 
in high-volatility trading environments. In a second step, we assess the 
relationship between implied volatility and forward looking stock index returns. 
There is some evidence that positive (negative) forward looking returns are to 
be expected for long positions triggered by extremely high (low) levels of the 
implied volatility indices.
'''


def initialize(context):
    context.security = symbol('SPY')  # Define a security for the following part
    context.index_VIX = superSymbol(secType='IND',
                                    symbol='VIX',
                                    currency='USD')  # Define the index
    # schedule_function is an IBridgePy function, also supported by Quantopian
    # date_rules.every_day : the dailyFunc will be run on every business day
    # time_rules.market_close(minutes=1) : the time to run dailyFunc is
    # 1 minute before U.S. market close (15:59:00 US/Eastern time)
    schedule_function(dailyFunc, date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_close(minutes=1))


def dailyFunc(context, data):
    hist = request_historical_data(context.index_VIX, '1 day', '732 D')
    currentVIX = show_real_time_price(context.index_VIX, 'last_price')
    twoYearMax = max(hist['close'])
    twoYearMin = min(hist['close'])
    if currentVIX > twoYearMax or currentVIX > 24.4:  # top 2 percentile boxes=24.4
        # condition 1: check if the VIX index on the current day is higher
        # than on any other day during the rolling 2 year window
        # condition 2: check if the VIX index value is in the highest
        # 2 percentile boxes
        # if condition 1 or condition 2 -> place long order

        orderId = order_target(context.security, 100)
        order_status_monitor(orderId, target_status='Filled')
    elif currentVIX < twoYearMin or currentVIX < 13.35:  # bottom percentile boxes=13.35
        # condition 3: check if the VIX index on the current day is lower
        # than on any other day during the rolling 2 year window
        # condition 4: check if the VIX index value is in the lowest
        # 2 percentile boxes
        # if condition 3 or contion 4 -> place short order
        orderId = order_target(context.security, -100)
        order_status_monitor(orderId, target_status='Filled')
    else:
        orderId = order_target(context.security, 0)
        order_status_monitor(orderId, target_status='Filled')
