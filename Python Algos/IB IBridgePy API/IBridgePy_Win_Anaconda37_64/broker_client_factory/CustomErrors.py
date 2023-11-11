# coding=utf-8
import sys


class CustomError(RuntimeError):
    """
    Custom Exception
    """
    def __init__(self, error_code, message):

        # Raise a separate exception in case the error code passed isn't specified in the ErrorCodes enum
        # if not isinstance(error_code, ErrorCodes):
        #     msg = 'Error code passed in the error_code param must be of type {0}'
        #     raise CustomError(ErrorCode.ERR_INCORRECT_ERRCODE, msg, ErrorCodes.__class__.__name__)

        # Storing the error code on the exception object
        self.error_code = error_code

        # storing the traceback which provides useful information about where the exception occurred
        self.traceback = sys.exc_info()
        self.message = message

    def __str__(self):
        return 'errorCode:%s %s' %(self.error_code, self.message)


class ErrorCodes(object):
    def __init__(self, code, message=''):
        self.code = code
        self.message = message

    def __str__(self):
        return self.code + ':' + self.message


# Error codes for all module exceptions
class ErrorCode(object):
    ERR_INCORRECT_ERRCODE = ErrorCodes(0, 'ERR_INCORRECT_ERRCODE')      # error code passed is not specified in enum ErrorCodes
    ERR_NOT_ENOUGH_FUND = ErrorCodes(9001, 'Not enough buying power to trade')          # description of situation 1
    ERR_NOT_ENOUGH_HIST = ErrorCodes(9002, 'Not enough historical data to backtest. Please check with data provider.')          # description of situation 1
    ERR_ORDER_STATUS_NOT_CONFIRMED = ErrorCodes(9003, 'Expected order status has not been confirmed by the broker')          # description of situation 1
    ERR_LOST_HEART_BEAT = ErrorCodes(9004, 'Lost heart beat.')


class LostHeartBeat(CustomError):
    def __init__(self):
        CustomError.__init__(self, ErrorCode.ERR_LOST_HEART_BEAT.code, ErrorCode.ERR_LOST_HEART_BEAT.message)


class NotEnoughFund(CustomError):
    def __init__(self):
        CustomError.__init__(self, ErrorCode.ERR_NOT_ENOUGH_FUND.code, ErrorCode.ERR_NOT_ENOUGH_FUND.message)


class NotEnoughHist(CustomError):
    def __init__(self):
        CustomError.__init__(self, ErrorCode.ERR_NOT_ENOUGH_HIST.code, ErrorCode.ERR_NOT_ENOUGH_HIST.message)


class OrderStatusNotConfirmed(CustomError):
    def __init__(self):
        CustomError.__init__(self, ErrorCode.ERR_ORDER_STATUS_NOT_CONFIRMED.code, ErrorCode.ERR_ORDER_STATUS_NOT_CONFIRMED.message)


if __name__ == '__main__':
    c = NotEnoughFund
    raise c
