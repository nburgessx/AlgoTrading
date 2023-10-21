# coding=utf-8
import requests
TD_AUTH_URL = 'https://api.tdameritrade.com/v1/oauth2/token'


def retrieve_access_token(refreshToken, client_id):
    """
    Retrieve ONLY access token from TD by a valid refresh token and client_id
    :param refreshToken: a valid refresh token that is valid for 90 days
    :param client_id: the created TD client id.
    :return: a url-decoded access token
    """
    resp = requests.post(TD_AUTH_URL,
                         headers={'Content-Type': 'application/x-www-form-urlencoded'},
                         data={'grant_type': 'refresh_token',
                               'refresh_token': refreshToken,
                               'client_id': client_id})
    if resp.status_code != 200:
        print(__name__ + '__init__::refresh_token: EXIT, error=%s' % (resp.content,))
        print('Hint: 1. Check if apikey is correct in settings.py. Refer to this tutorial https://youtu.be/l3qBYMN4yMs')
        print('Hint: 2. Check if refreshToken is correct in settings.py. It is pretty long, and should be url decoded.')
        print('Hint: 3: Refresh token is valid up to 90 days. Create a new refresh token when needed. https://youtu.be/Ql6VnR0GIYY')
        raise RuntimeError('Could not authenticate! error=%s' % (resp.content,))
    return resp.json()['access_token']


def renew_refresh_token(refreshToken, client_id):
    access_token = retrieve_access_token(refreshToken, client_id)
    return renew_refresh_token_by_access_toen_and_refresh_token(refreshToken, client_id, access_token)


def renew_refresh_token_by_access_toen_and_refresh_token(refreshToken, client_id, access_token):
    """
    Renew refresh token from TD by a valid refresh token and client_id
    :param access_token: a fresh access token, which can be retrieved by auth.retrieve_access_token
    :param refreshToken: a valid refresh token that is valid for 90 days
    :param client_id: the created TD client id.
    :return: a url-decoded refresh token
    """
    resp = requests.post(TD_AUTH_URL,
                         headers={'Content-Type': 'application/x-www-form-urlencoded'},
                         data={'grant_type': 'refresh_token',
                               'refresh_token': refreshToken,
                               'access_type': 'offline',
                               'code': access_token,
                               'client_id': client_id,
                               'redirect_url': 'http://localhost:8080/'})
    if resp.status_code != 200:
        raise RuntimeError('Could not authenticate! error=%s' % (resp.content,))
    return resp.json()['refresh_token']
