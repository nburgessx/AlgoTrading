# coding=utf-8
import datetime as dt
import time
from sys import exit

from broker_client_factory.BrokerClientDefs import ReqMktData, ReqPositions, ReqAllOpenOrders, ReqAccountUpdates, \
    ReqOneOrder
from broker_client_factory.CustomErrors import OrderStatusNotConfirmed
from broker_service_factory.BrokerService import BrokerService
from models.utils import print_IBCpp_contract


class RequestRecorder(object):
    """
    WebApi needs to record some requests to Broker to avoid query too much and too soon.
    """
    def __init__(self):
        self._request_recorder = {}

    def hasRecentRequest(self, request, freshness_in_microseconds):  # Don't query broker if the same request was sent recently
        str_requestName = str(request)
        # if there is no previous request, record the request datetime
        if str_requestName not in self._request_recorder:
            self._request_recorder[str_requestName] = dt.datetime.now()
            return False
        else:
            # print(__name__ + '::hasRecentRequest: get from cache')
            now = dt.datetime.now()
            ans = (now - self._request_recorder[str_requestName]).microseconds <= freshness_in_microseconds

            # If found the previous request within 5 seconds, don't record request datetime,
            # otherwise, the record cannot recover if incoming request every 1 second.
            if not ans:
                self._request_recorder[str_requestName] = now
            return ans


# noinspection PyAbstractClass
class WebApi(BrokerService):
    _request_recorder = RequestRecorder()

    @property
    def name(self):
        return 'WebApi'

    @property
    def brokerName(self):
        """
        Name of the broker

        :return: string name
        """
        raise NotImplementedError(self.name)

    def _submit_request_after_checking_cache(self, request, freshness_in_microseconds=90000):
        if not self._request_recorder.hasRecentRequest(request, freshness_in_microseconds):
            self._log.debug(__name__ + '::_submit_request_after_checking_cache: submit_requests')
            self.submit_requests(request)
            return True
        else:
            self._log.debug(__name__ + '::_submit_request_after_checking_cache: submit_requests ignored')
            return False

    def get_real_time_price(self, security, tickType, followUp=True):  # return real time price
        self._log.notset(__name__ + '::get_real_time_price: security=%s tickType=%s' % (security.full_print(), tickType))
        self._submit_request_after_checking_cache(ReqMktData(security, followUp=followUp))
        return self._get_real_time_price_from_dataFromServer(security, tickType)

    def get_real_time_size(self, security, tickType, followUp=True):  # return real time price
        self._log.debug(__name__ + '::get_real_time_size: security=%s tickType=%s' % (security, tickType))
        self._submit_request_after_checking_cache(ReqMktData(security, followUp=followUp))
        return self._get_real_time_size_from_dataFromServer(security, tickType)

    def get_position(self, accountCode, security):
        self.submit_requests(ReqPositions())
        return self._get_position(accountCode, security)

    def get_all_orders(self, accountCode):
        self._log.debug(__name__ + '::get_all_orders: accountCode=%s' % (accountCode,))
        # Web-api-based brokers may not have all order info. For example, TD only keeps the orders for the latest 7 days.
        # And get_all_orders from broker will only return recent orders.
        # It means that orders' latest status may not be updated if the order was placed a few days ago.
        # The solution is to delete every order and request latest order info from broker.
        self._singleTrader.delete_every_order(self.brokerName, accountCode)
        self._submit_request_after_checking_cache(ReqAllOpenOrders())
        return self._get_all_orders(accountCode)

    def get_all_positions(self, accountCode):
        """
        Get all of positionRecords associated with the accountCode
        :param accountCode:
        :return: dictionary, keyed by Security object with exchange info!!!, value = PositionRecord
        """
        self._log.debug(__name__ + '::get_all_positions: accountCode=%s' % (accountCode,))
        # When algo runs continuously, after a position is sell-off, the position will stay in keyedPositionRecords
        # because get_all_positions() will not have that position anymore and the record in keyedPositionRecords will not
        # be updated anymore. The solution is to delete all positions before get_all_position so that positions are always fresh
        self._singleTrader.delete_every_position(self.brokerName, accountCode)
        self.submit_requests(ReqPositions())
        return self._get_all_positions(accountCode)

    def get_order(self, ibpyOrderId):
        """

        :param ibpyOrderId: int
        :return: broker_factory::records_def::IBridgePyOrder
        """
        self._log.notset(__name__ + '::get_order: ibpyOrderId=%s' % (ibpyOrderId,))
        self.submit_requests(ReqAllOpenOrders())
        accountCode = self._singleTrader.get_accountCode_by_ibpyOrderId(self.brokerName, ibpyOrderId)
        return self._singleTrader.find_order(self.brokerName, accountCode, ibpyOrderId)

    # noinspection DuplicatedCode
    def _get_account_info_one_tag(self, accountCode, tag, meta='value'):
        self._submit_request_after_checking_cache(ReqAccountUpdates(True, accountCode))
        self.submit_requests(ReqAccountUpdates(True, accountCode))
        # noinspection DuplicatedCode
        ans = self._singleTrader.get_account_info(self.brokerName, accountCode, tag)
        if ans is None:
            self._log.error(__name__ + '::_get_account_info_one_tag: EXIT, no value based on accountCode=%s tag=%s' % (accountCode, tag))
            print('active accountCode is %s' % (self._singleTrader.get_all_active_accountCodes(self.brokerName),))
            exit()
        return ans

    def order_status_monitor(self, ibpyOrderId, target_status, waitingTimeInSeconds=30):
        self._log.debug(__name__ + '::order_status_monitor: ibpyOrderId=%s target_status=%s' % (ibpyOrderId, target_status))
        timer = dt.datetime.now()
        while True:
            time.sleep(1)  # Do not send too much request to TD max=120 requests/minute
            self._submit_request_after_checking_cache(ReqOneOrder(ibpyOrderId))

            if (dt.datetime.now() - timer).total_seconds() <= waitingTimeInSeconds:
                tmp_status = self.get_order(ibpyOrderId).status
                if isinstance(target_status, str):
                    if tmp_status == target_status:
                        return
                elif isinstance(target_status, list):
                    if tmp_status in target_status:
                        return
            else:
                self._log.error(__name__ + '::order_status_monitor: EXIT, waiting time is too long, >%s' % (waitingTimeInSeconds,))
                order = self.get_order(ibpyOrderId)
                contract = order.contract
                self._log.error(__name__ + '::order_status_monitor: EXIT, ibpyOrderId=%s status=%s contract=%s' % (ibpyOrderId, order.status, print_IBCpp_contract(contract)))
                raise OrderStatusNotConfirmed()
