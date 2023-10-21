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

# Introduction to request_historical_data. YouTube tutorial https://youtu.be/7jmHRVsRcI0
# Request historical data of other than U.S. equities and handle 'No data permission' and 'No security definition'. YouTube tutorial https://youtu.be/iiRierq6sTU
# Request historical data of FOREX, provided by Interactive Brokers for free. YouTube tutorial https://youtu.be/7jmHRVsRcI0
# If you need help on coding, please consider our well known Rent-a-Coder service. https://ibridgepy.com/rent-a-coder/
def initialize(context):
    # IB offers free historical data for FOREX. Please refer to this YouTube tutorial https://youtu.be/JkyxLYD2RBk
    context.security = symbol('SPY')
    context.secList = symbols('AAPL', 'GOOG')


def handle_data(context, data):
    # Method 1: IBridgePy function request_historical_data(str_security, barSize, goBack)
    # Users have more controls on this function.
    # http://www.ibridgepy.com/ibridgepy-documentation/#request_historical_data
    print ('Historical Data of %s' % (str(context.security, ),))
    hist = request_historical_data(context.security, '1 day', '5 D')
    print(hist)
    print(hist.iloc[-1]['close'])

    # Method 2 Same as Quantopian's function
    # http://www.ibridgepy.com/ibridgepy-documentation/#datahistory_8212_similar_as_datahistory_at_Quantopian
    # data.history(str_security, fields, bar_count, frequency)
    hist = data.history(context.secList, ['open', 'high', 'low', 'close'], 5, '1d')
    for i in range(len(context.secList)):
        print ('Historical Data CLOSE of %s' % (str(context.secList[i], ),))
        print (hist['close'][context.secList[i]])
    end()
