import six

if six.PY3:
    from broker_client_factory import Robinhood
else:
    from Robinhood import Robinhood
    import exceptions as RH_exception
