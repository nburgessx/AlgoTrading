#!/usr/bin/python
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

from IBridgePy.constants import BrokerClientName
from broker_client_factory.BrokerClient_IB import ClientIB


# noinspection PyAbstractClass
class IBRegular(ClientIB):
    # !!!
    # DO NOT implement __init___ here. It will override IBCpp.__init__ and cause many errors

    @property
    def name(self):
        return BrokerClientName.IB

    def placeOrderWrapper(self, contract, ibcppOrder, ibpyRequest):
        self._log.debug(f"{__name__}::placeOrderWrapper:: contract={contract} ibcppOrder={ibcppOrder} ibpyRequest={ibpyRequest}")
        if ibcppOrder.get('orderId', None) is None:
            int_orderId = self.use_next_id()
            ibcppOrder.orderId = int_orderId
        else:
            if isinstance(ibcppOrder['orderId'], int):
                int_orderId = ibcppOrder['orderId']
            else:
                int_orderId = int(ibcppOrder['orderId'])
        self._placeOrderHelper(int_orderId, ibpyRequest, contract, ibcppOrder)
