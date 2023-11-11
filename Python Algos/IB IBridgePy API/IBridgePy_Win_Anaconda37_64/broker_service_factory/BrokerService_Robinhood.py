# coding=utf-8
from IBridgePy.constants import BrokerServiceName, BrokerName
from broker_service_factory.BrokerService_web import WebApi


class Robinhood(WebApi):
    def get_scanner_results(self, kwargs):
        raise NotImplementedError(self.name)

    def get_timestamp(self, security, tickType):
        raise NotImplementedError(self.name)

    def get_contract_details(self, security, field, waitForFeedbackInSeconds=30):
        raise NotImplementedError(self.name)

    def get_option_info(self, security, fields, waitForFeedbackInSeconds=30):
        raise NotImplementedError(self.name)

    @property
    def name(self):
        return BrokerServiceName.ROBINHOOD

    @property
    def brokerName(self):
        return BrokerName.ROBINHOOD
