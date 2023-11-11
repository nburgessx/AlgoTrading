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
    context.flag = False
    context.sec1 = symbol('CASH,EUR,USD')
    context.sec2 = symbol('CASH,GBP,USD')
    context.sec3 = symbol('CASH,USD,JPY')
    context.accountCodeList = ['DU812752', 'DU812675', 'DU812678']


def handle_data(context, data):
    if not context.flag:
        orderId1 = order(context.sec1, 100, accountCode=context.accountCodeList[0])
        orderId2 = order(context.sec2, 200, accountCode=context.accountCodeList[1])
        orderId3 = order(context.sec3, 300, accountCode=context.accountCodeList[2])
        order_status_monitor(orderId1, target_status='Filled')
        order_status_monitor(orderId2, target_status='Filled')
        order_status_monitor(orderId3, target_status='Filled')
        context.flag = True

    else:
        display_all(context.accountCodeList[0])
        display_all(context.accountCodeList[1])
        display_all(context.accountCodeList[2])
        exit()
