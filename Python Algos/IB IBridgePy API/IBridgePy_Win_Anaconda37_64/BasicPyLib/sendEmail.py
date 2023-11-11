# coding=utf-8
import requests
from requests.exceptions import ConnectionError
import time


class IbpyEmailClient(object):
    DOMAIN = 'ibridgepy-portal.herokuapp.com'
    TEST_DOMAIN = '127.0.0.1:8000'
    PROTOCOL = 'https://'
    TEST_PROTOCOL = 'http://'

    def __init__(self, apiKey, log=None, isTest=False):
        assert(isinstance(apiKey, str))
        self.apiKey = apiKey
        self._log = log
        if isTest:
            self.urlRoot = '%s%s/handleEmail/api?apiKey=%s' % (self.TEST_PROTOCOL, self.TEST_DOMAIN, self.apiKey,)
        else:
            self.urlRoot = '%s%s/handleEmail/api?apiKey=%s' % (self.PROTOCOL, self.DOMAIN, self.apiKey,)

    def send_email(self, emailTitle, emailBody, toEmail=None):
        if toEmail:
            URL = self.urlRoot + '&toEmail=%s&emailTitle=%s&emailBody=%s' % (toEmail, emailTitle, emailBody)
        else:
            URL = self.urlRoot + '&emailTitle=%s&emailBody=%s' % (emailTitle, emailBody)
        count = 0
        err = None
        while count < 3:
            count += 1
            try:
                response = requests.get(url=URL)
                return response
            except ConnectionError as e:
                err = e
                time.sleep(5)
        if self._log:
            self._log.error(__name__ + '::send_email: URL=%s and err=%s' % (URL, err))
            # Don't exit, just write to log
        return 'Failed to send email. Something is wrong.'
