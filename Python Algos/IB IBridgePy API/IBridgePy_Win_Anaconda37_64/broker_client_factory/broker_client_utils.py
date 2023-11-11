# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:50:16 2017

@author: IBridgePy@gmail.com
"""
from sys import exit

from IBridgePy.constants import BrokerClientName


class Converter(object):
    """
    IB uses integer as orderId and it must increase.
    Other brokers use string as orderId.
    And IBridgePy has switched from int_orderId to str_orderId.
    For IB, str_orderId = 'ib' + int_orderId
    For other brokers, use broker's original str_orderId
    """

    def __init__(self, brokerClientName, createrOfIBValue=None):
        self._brokerClientName = brokerClientName
        self._fromBrokerToIBDict = {}
        self._fromIBToBrokerDict = {}
        self._createrOfIBValue = createrOfIBValue

    def fromBrokerToIB(self, brokerValue):
        """
        Converter a str_orderId to int_orderId
        :param brokerValue: string
        :return: int
        """
        if brokerValue in self._fromBrokerToIBDict:
            return self._fromBrokerToIBDict[brokerValue]
        ibValue = None
        if self._brokerClientName in [BrokerClientName.IB, BrokerClientName.LOCAL, BrokerClientName.IBinsync]:
            ibValue = int(brokerValue)
        elif self._brokerClientName in [BrokerClientName.TD, BrokerClientName.ROBINHOOD]:
            # useOne() for IB should be updated from IB servery every time before use.
            # Here, useOne() is not updated from broker server. However, it won't cause any trouble because of TD and Robinhood
            ibValue = self._createrOfIBValue.useOne()
        else:
            print(__name__ + '::Converter::fromBrokerToIB: EXIT, cannot handle brokerServiceName=%s' % (self._brokerClientName,))
            exit()
        self.setRelationship(ibValue, brokerValue)
        return ibValue

    def fromIBtoBroker(self, ibValue):
        """
        Converter a int_orderId to str_orderId
        :param ibValue: int
        :return: string
        """
        # For non-IB orders, they should have been registered in brokerClient_xx using setRelationship
        if ibValue in self._fromIBToBrokerDict:
            return self._fromIBToBrokerDict[ibValue]

        if self._brokerClientName in [BrokerClientName.IB, BrokerClientName.LOCAL, BrokerClientName.IBinsync]:
            brokerValue = 'ib' + str(ibValue)
            self.setRelationship(ibValue, brokerValue)
            return brokerValue
        else:
            print(
                    __name__ + '::Converter::fromBrokerToIB: EXIT, For non-IB orders, they should have been registered in brokerClient_xx using setRelationship')
            exit()

    def setRelationship(self, ibValue, brokerValue):
        # print(__name__ + '::Converter::setRelationship: ibValue=%s brokerValue=%s' % (ibValue, brokerValue))
        self._fromBrokerToIBDict[brokerValue] = ibValue
        self._fromIBToBrokerDict[ibValue] = brokerValue

    def verifyRelationship(self, ibValue, brokerValue):
        ans = (ibValue in self._fromIBToBrokerDict) and (brokerValue in self._fromBrokerToIBDict) and (
                self._fromIBToBrokerDict[ibValue] == brokerValue)
        if not ans:
            print(__name__ + '::Converter::verifyRelationship: EXIT, ibValue=%s brokerValue=%s' % (
                ibValue, brokerValue))
            print(self._fromIBToBrokerDict)
            print(self._fromBrokerToIBDict)
            exit()
