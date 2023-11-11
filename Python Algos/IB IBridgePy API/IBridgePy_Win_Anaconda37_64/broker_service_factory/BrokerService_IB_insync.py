# coding=utf-8
# noinspection PyUnresolvedReferences
from IBridgePy import IBCpp
from IBridgePy.constants import BrokerServiceName, BrokerName
from broker_client_factory.BrokerClientDefs import ReqAccountUpdates
from broker_service_factory.BrokerService_web import WebApi
from sys import exit


class IBinsync(WebApi):
    def get_timestamp(self, security, tickType):
        raise NotImplementedError

    def get_option_greeks(self, security, tickType, fields):
        self._log.debug(__name__ + '::get_option_greeks: security=%s tickType=%s fields=%s'
                        % (security.full_print(), str(tickType), str(fields)))
        ans = {}
        for fieldName in fields:
            ans[fieldName] = self._dataFromServer.get_value(security, tickType, fieldName)
        return ans

    def get_contract_details(self, security, field, waitForFeedbackInSeconds=30):
        self._log.debug(__name__ + '::get_contract_details: security=%s field=%s' % (security, field))
        return self._brokerClient.get_contract_details(security, field, waitForFeedbackInSeconds=waitForFeedbackInSeconds)

    @property
    def name(self):
        return BrokerServiceName.IBinsync

    @property
    def brokerName(self):
        return BrokerName.IB

    # noinspection DuplicatedCode
    def _get_account_info_one_tag(self, accountCode, tag, meta='value'):
        self._log.notset(__name__ + '::_get_account_info_one_tag: accountCode=%s tag=%s' % (accountCode, tag))
        submitted = self._submit_request_after_checking_cache(ReqAccountUpdates(True, accountCode))
        # noinspection DuplicatedCode
        ans = self._singleTrader.get_account_info(self.brokerName, accountCode, tag)
        if ans is None:
            self._log.error('EXIT, no value based on accountCode=%s tag=%s' % (accountCode, tag))
            self._log.error('Active accountCodes are %s' % (self._singleTrader.get_all_active_accountCodes(self.brokerName),))
            exit()
        if submitted:
            self.submit_requests(ReqAccountUpdates(False, accountCode))
        return ans
