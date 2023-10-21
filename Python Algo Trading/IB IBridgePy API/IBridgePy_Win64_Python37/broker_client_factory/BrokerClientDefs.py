# coding=utf-8
from BasicPyLib.BasicTools import CONSTANTS, Timer
from models.utils import print_IBCpp_order, print_IBCpp_contract
from sys import exit
import pandas as pd
import pytz


class IgnoringError(CONSTANTS):
    ERROR_IS_IGNORED = True
    ERROR_NEEDS_ATTENTION = False


class ReqAttr(CONSTANTS):
    class Status(CONSTANTS):
        COMPLETED = 'Completed'
        CREATED = 'Created'
        SUBMITTED = 'Submitted'
        STARTED = 'Started'

    class FollowUp(CONSTANTS):
        FOLLOW_UP = True
        DO_NOT_FOLLOW_UP = False


class ReqHistParam(CONSTANTS):
    class Name(CONSTANTS):
        BAR_SIZE = 'barSize'
        GO_BACK = 'goBack'
        END_TIME = 'endTime'

    class BarSize(CONSTANTS):
        ONE_MIN = '1 min'
        ONE_DAY = '1 day'

    class GoBack(CONSTANTS):
        ONE_DAY = '1 D'
        FIVE_DAYS = '5 D'

    class FormatDate(CONSTANTS):
        DATE_TIME = 1
        UTC_SECOND = 2

    class UseRTH(CONSTANTS):
        DATA_IN_REGULAR_HOURS = 1
        ALL_DATA = 0


class ActiveRequestBatch(object):
    def __init__(self, requests, uuid):  # uuid is broker_client_factory::BrokerClient::Uuid
        self.nextReqId = uuid

        # Must use list to keep the sequence of requestRecord because a list of reqID needs to be returned
        # the returned reqId list will be used to retrieve results
        self._requestIdList = []

        # use dict here for quick search by reqId
        self.activeRequestsDict = {}

        # check if any request has failed based on waitingInSecond
        self.timer = Timer()

        for request in requests:
            self._add(request)

    def __str__(self):
        ans = ''
        for reqId in self.get_request_ids():
            ans += str(self.activeRequestsDict[reqId]) + '\n'
        return ans[:-1]

    def is_reqId_within_activeRequests(self, reqId):
        return reqId in self.activeRequestsDict

    def get_request_ids(self):
        return self._requestIdList

    def _add(self, aRequest):
        """
        Use nextReqId as Key, called reqId, use aRequest as Value
        :param aRequest: ReqDataBase
        :return: None
        """
        reqId = self.nextReqId.useOne()
        self._requestIdList.append(reqId)
        self.activeRequestsDict[reqId] = aRequest
        aRequest.reqId = reqId

    def has_reqId(self, reqId):
        return reqId in self.activeRequestsDict

    def get_by_reqId_otherwise_exit(self, reqId):
        if reqId in self.activeRequestsDict:
            return self.activeRequestsDict[reqId]
        else:
            print(__name__ + '::get_by_reqId_otherwise_exit: EXIT reqId=%s' % (reqId,))
            self.print_activeRequest()
            exit()

    def find_reqId_by_int_orderId(self, int_orderId):
        """

        :param int_orderId:
        :return: reqId if found, Otherwise return None. It is normal that reqId is not found when order is not place in this session.
        """
        for reqId in self.activeRequestsDict:
            if 'int_orderId' in self.activeRequestsDict[reqId].param:
                if int_orderId == self.activeRequestsDict[reqId].param['int_orderId']:
                    return reqId
                else:
                    pass
                    # DO NOT DELETE, for debug
                    # print(__name__ + '::ActiveRequestBatch::find_reqId_by_int_orderId: reqId=%s checking param[int_orderid]=%s' % (reqId, self.activeRequestsDict[reqId].param['int_orderId']))
            else:
                pass
                # DO NOT DELETE, for debug
                # print(__name__ + '::ActiveRequestBatch::find_reqId_by_int_orderId: reqId=%s cannot find param[int_orderid]' % (reqId,))

        return None

    def find_a_reqId_by_reqType_otherwise_exit(self, reqType):
        """

        :param reqType: string
        :return: a list of reqIds
        """
        # print(__name__ + '::find_a_reqId_by_reqType_otherwise_exit: reqType=%s' % (reqType,))
        for reqId in self.activeRequestsDict:
            if self.activeRequestsDict[reqId].reqType == reqType:
                return reqId
        print(__name__ + '::find_a_reqId_by_reqType_otherwise_exit: EXIT reqType=%s' % (reqType,))
        self.print_activeRequest()
        exit()

    def ignoringErrorCode(self, reqId, errorCode):
        if self.activeRequestsDict[reqId].ignoringAllErros:
            return IgnoringError.ERROR_IS_IGNORED
        if errorCode in self.activeRequestsDict[reqId].ignoringTheseErrors:
            return IgnoringError.ERROR_IS_IGNORED
        return IgnoringError.ERROR_NEEDS_ATTENTION

    def check_all_completed(self):
        for reqId in self.activeRequestsDict:
            if self.activeRequestsDict[reqId].status != ReqAttr.Status.COMPLETED:
                return False
        return True

    def find_failed_requests(self):
        ans = []
        for reqId in self.activeRequestsDict:
            aRequest = self.activeRequestsDict[reqId]
            if aRequest.status != ReqAttr.Status.COMPLETED:
                if self.timer.elapsedInSecond() > aRequest.waitForFeedbackInSeconds:
                    ans.append(reqId)
        return ans

    def label_uncompleted_to_completed_if_not_followup(self):
        # print(f'{__name__}::label_uncompleted_to_completed_if_not_followup')
        for reqId in self.activeRequestsDict:
            aRequest = self.activeRequestsDict[reqId]
            if aRequest.status != ReqAttr.Status.COMPLETED:
                if self.timer.elapsedInSecond() > aRequest.waitForFeedbackInSeconds:
                    if aRequest.followUp is False:
                        aRequest.status = ReqAttr.Status.COMPLETED
                        print(f'{aRequest} is changed from uncompleted to completed because followUp=False.')

    def _find_reqIds_by_reqType(self, reqType):
        ans = []
        for reqId in self.activeRequestsDict:
            if self.activeRequestsDict[reqId].reqType == reqType:
                ans.append(reqId)
        return ans

    def set_a_request_of_a_reqId_to_a_status(self, reqId, status):
        if reqId in self.activeRequestsDict:
            self.activeRequestsDict[reqId].status = status

    def set_a_request_of_an_orderId_to_a_status(self, orderId, status):
        reqId = self.find_reqId_by_int_orderId(orderId)
        if reqId is not None:
            self.activeRequestsDict[reqId].status = status

    def set_all_requests_of_a_reqType_to_a_status(self, reqType, status):
        reqIdList = self._find_reqIds_by_reqType(reqType)
        for reqId in reqIdList:
            self.activeRequestsDict[reqId].status = status

    def set_all_requests_of_a_reqType_to_a_status_and_set_result(self, reqType, status, result):
        reqIdList = self._find_reqIds_by_reqType(reqType)
        for reqId in reqIdList:
            self.activeRequestsDict[reqId].status = status
            self.activeRequestsDict[reqId].returnedResult = result

    def print_activeRequest(self):
        for reqId in self.activeRequestsDict:
            print(__name__ + '::print_activeRequest')
            print(self.activeRequestsDict[reqId])


class Request(object):
    def __init__(self, reqType, followUp=ReqAttr.FollowUp.FOLLOW_UP, status=ReqAttr.Status.CREATED,
                 waitForFeedbackInSeconds=30):
        self.status = status
        self.reqId = None
        self.reqType = reqType
        self.followUp = followUp  # if followUp False, IBridgePy will not check if the result of request has been received
        self.param = {}  # all request input are saved here.
        self.ignoringAllErrors = False
        self.ignoringTheseErrors = set()
        self.numberOfTotalSending = 1
        self.currentNumberOfSending = 0
        self.returnedResult = None
        self.waitForFeedbackInSeconds = waitForFeedbackInSeconds

    def __str__(self):
        ans = '{reqId=%s,status=%s,reqType=%s,followUp=%s,waitForFeedbackInSeconds=%s,' % (self.reqId, self.status, self.reqType, self.followUp, self.waitForFeedbackInSeconds)
        tmp = '{'
        for key in self.param:
            if key == 'order':
                tmp += 'order:%s,' % (print_IBCpp_order(self.param[key]))
            elif key == 'contract':
                tmp += 'contract:%s,' % (print_IBCpp_contract(self.param[key]))
            elif key == 'security':
                tmp += 'security:%s,' % (self.param[key].full_print())
            else:
                tmp += '%s:%s,' % (key, self.param[key])
        tmp += '}'
        ans += 'param=%s}' % (tmp,)
        return ans


class ReqConnect(Request):
    def __init__(self, waitForFeedbackInSeconds=3):
        Request.__init__(self, reqType='reqConnect', waitForFeedbackInSeconds=waitForFeedbackInSeconds)


class ReqPositions(Request):
    def __init__(self):
        Request.__init__(self, reqType='reqPositions')
        self.returnedResult = pd.DataFrame()  # prepare default returned result


class ReqAccountUpdates(Request):
    def __init__(self, subscribe, accountCode):
        """
        constructor
        :param subscribe: bool, should be true for most of time
        :param accountCode: string
        """
        Request.__init__(self, reqType='reqAccountUpdates')
        self.param['subscribe'] = subscribe
        self.param['accountCode'] = accountCode


class ReqAccountSummary(Request):
    def __init__(self, group='All', tag='TotalCashValue,GrossPositionValue,NetLiquidation'):
        Request.__init__(self, reqType='reqAccountSummary')
        self.param['group'] = group
        self.param['tag'] = tag


class ReqIds(Request):
    def __init__(self):
        Request.__init__(self, reqType='reqIds')


class ReqHeartBeats(Request):
    def __init__(self, waitForFeedbackInSeconds=10):
        Request.__init__(self, reqType='reqHeartBeats', waitForFeedbackInSeconds=waitForFeedbackInSeconds)


class ReqOneOrder(Request):
    """
    Only available to TD Ameritrade
    """
    def __init__(self, orderId):
        Request.__init__(self, reqType='reqOneOrder')
        self.param['orderId'] = orderId


class ReqAllOpenOrders(Request):
    def __init__(self):
        Request.__init__(self, reqType='reqAllOpenOrders')


class ReqCurrentTime(Request):
    def __init__(self):
        Request.__init__(self, reqType='reqCurrentTime')


class ReqHistoricalData(Request):
    def __init__(self, security,
                 barSize,
                 goBack,
                 endTime,
                 whatToShow,
                 useRTH=ReqHistParam.UseRTH.DATA_IN_REGULAR_HOURS,
                 formatDate=ReqHistParam.FormatDate.UTC_SECOND,
                 waitForFeedbackInSeconds=30,
                 timezoneOfReturn=pytz.timezone('US/Eastern'),
                 followUp=True):
        Request.__init__(self, reqType='reqHistoricalData', waitForFeedbackInSeconds=waitForFeedbackInSeconds, followUp=followUp)
        self.param['security'] = security
        # string barSize: 1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins,
        # 3 mins, 5 mins, 15 mins, 30mins, 1 hour, 1 day
        self.param['barSize'] = barSize

        # S (seconds), D (days), W (week), M(month) or Y(year).
        self.param['goBack'] = goBack
        self.param['endTime'] = endTime  # string with timezone or empty string
        self.param['whatToShow'] = whatToShow
        self.param['useRTH'] = useRTH
        self.param['formatDate'] = formatDate
        self.param['timezoneOfReturn'] = timezoneOfReturn
        self.returnedResult = pd.DataFrame()  # prepare default returned result


class ReqMktData(Request):
    def __init__(self, security, tickTypeClientAsked=None, genericTickList='101', snapshot=False, followUp=True, waitForFeedbackInSeconds=30):
        Request.__init__(self, reqType='reqMktData', waitForFeedbackInSeconds=waitForFeedbackInSeconds)
        self.param['security'] = security
        self.param['genericTickList'] = genericTickList
        self.param['snapshot'] = snapshot
        self.param['tickTypeClientAsked'] = tickTypeClientAsked
        self.followUp = followUp


class CancelMktData(Request):
    def __init__(self, security):
        Request.__init__(self, reqType='cancelMktData')
        self.param['security'] = security
        self.followUp = False  # IB never confirm cancelMktData


class ReqRealTimeBars(Request):
    def __init__(self, security, whatToShow, barSize=5, useRTH=True, followUp=True):
        Request.__init__(self, reqType='reqRealTimeBars')
        self.param['security'] = security
        self.param['barSize'] = barSize
        self.param['whatToShow'] = whatToShow
        self.param['useRTH'] = useRTH
        self.followUp = followUp


class ReqContractDetails(Request):
    def __init__(self, security, waitForFeedbackInSeconds=120):
        Request.__init__(self, reqType='reqContractDetails', waitForFeedbackInSeconds=waitForFeedbackInSeconds)
        self.param['security'] = security
        self.returnedResult = pd.DataFrame()  # prepare default returned result


class CalculateImpliedVolatility(Request):
    def __init__(self, security, optionPrice, underPrice):
        Request.__init__(self, reqType='calculateImpliedVolatility')
        self.param['security'] = security
        self.param['optionPrice'] = optionPrice
        self.param['underPrice'] = underPrice


class PlaceOrder(Request):
    def __init__(self, contract, order, followUp, waitForFeedbackInSeconds=30):
        Request.__init__(self, reqType='placeOrder', followUp=followUp, waitForFeedbackInSeconds=waitForFeedbackInSeconds)
        self.param['contract'] = contract
        self.param['order'] = order


class ModifyOrder(Request):
    def __init__(self, ibpyOrderId, contract, order, followUp, waitForFeedbackInSeconds=30):
        Request.__init__(self, reqType='modifyOrder', followUp=followUp, waitForFeedbackInSeconds=waitForFeedbackInSeconds)
        self.param['ibpyOrderId'] = ibpyOrderId
        self.param['contract'] = contract
        self.param['order'] = order


class ReqScannerSubscription(Request):
    def __init__(self, subscription, tagValueList='default', waitForFeedbackInSeconds=30):
        Request.__init__(self, reqType='reqScannerSubscription', waitForFeedbackInSeconds=waitForFeedbackInSeconds)
        self.param['subscription'] = subscription
        if tagValueList == 'default':
            self.param['tagValueList'] = []  # TODO: IBCpp needs upgrade here
        else:
            self.param['tagValueList'] = tagValueList  # TODO: IBCpp needs upgrade here
        self.returnedResult = pd.DataFrame()  # prepare default returned result


class CancelScannerSubscription(Request):
    def __init__(self, scannerReqId, followUp=False):
        Request.__init__(self, reqType='cancelScannerSubscription', followUp=followUp)
        self.param['tickerId'] = scannerReqId


class CancelOrder(Request):
    def __init__(self, ibpyOrderId):
        Request.__init__(self, reqType='cancelOrder')
        self.param['ibpyOrderId'] = ibpyOrderId
        self.param['int_orderId'] = None  # Ending flag in orderStatus. it will search reqId by int_orderId


class ReqScannerParameters(Request):
    def __init__(self):
        Request.__init__(self, reqType='reqScannerParameters')
