'''
Created on Dec 18, 2016
@author: Yvictor
'''


class CrawlerError(Exception):
    def __init__(self, message, data={}):
        self.message = message
        self.data = data

    def __str__(self):
        return self.message


import requests
import traceback
import os
import logging as origin_log
import raven
from raven.handlers.logging import SentryHandler


class Logger():
    _TYPE_SENTRY = 0
    def __init__(self, lgrname):
        self._logtype = []
        self._lgrname = lgrname
        self._logger = origin_log.getLogger(lgrname)
        if origin_log.StreamHandler not in [type(handler) for handler in self._logger.handlers]:
            ch = origin_log.StreamHandler()
            ch.setLevel(origin_log.DEBUG)
            ch.setFormatter(origin_log.Formatter('%(levelname)s:\n    %(asctime)s\n    Worker:"%(name)s"\n    %(message)s'))
            self._logger.addHandler(ch)


    def init_sentry(self, sentry_dns):
        self._logtype.append(self._TYPE_SENTRY)
        client = raven.Client(dns=sentry_dns)
        sentry_handler = SentryHandler(client)
        if SentryHandler not in [type(handler) for handler in self._logger.handlers]:
            self._logger.addHandler(sentry_handler)


    def save_log_data(self, errlv, errname, errdes, errdata):
        if errlv in ['debug', 'info', 'warning', 'error', 'critical']:
            if self._TYPE_SENTRY not in self._logtype:
                getattr(self._logger, errlv)('%s: %s\n    %s' % (errname, errdes, errdata['traceback']))
            else:
                getattr(self._logger, errlv)('%s: %s\n    %s' % (errname, errdes, errdata['traceback']), exc_info=True, extra={
                    'errlv': errlv,
                    'woker': self._lgrname,
                    'errname': errname,
                    'errdes': errdes,
                    'errdata': errdata
                })


    @classmethod
    def from_env_var(cls):
        lgrname = os.environ.get('WORKER_NAME', 'NoWorkerName')
        s = cls(lgrname)

        SENTRY_DNS = os.environ.get('SENTRY_DNS','https://74c671b467e44539b432644ea4b240c3:0b9cee44e80a4c01a6589ac83dd4a2c1@sentry.io/123918')
        if SENTRY_DNS != '':
            s.init_sentry('https://74c671b467e44539b432644ea4b240c3:0b9cee44e80a4c01a6589ac83dd4a2c1@sentry.io/123918')
        return s


""" logging error
    errlv: debug, info, warning, error, critical
    errname: class name of the exception object or title of the error
    errdes: description of the error
    errdata: a dictionary
"""
def logging(errlv, errname, errdes, errdata, logger):
    errdata['traceback'] = traceback.format_exc()
    logger.save_log_data(errlv, errname, errdes, errdata)


def _log_error(errobj, errdes, errdata, logger):
    errdata['errobj'] = errobj
    logging('error', errobj.__class__.__name__, errdes, errdata, logger)


def func_logging(raise_exp):
    def decorator(func):
        logger = Logger.from_env_var()
        def new_func(*args, **kwargs):
            errdata = {
                'func_name': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            res = None
            try:
                res = func(*args, **kwargs)
            except requests.HTTPError as e:
                errdes = '%s; method: %s; url: %s' % (e.message, e.request.method, e.response.url)
                _log_error(e, errdes, errdata, logger)
                if raise_exp:
                    raise e
            except CrawlerError as e:
                errdes = e.message
                _log_error(e, errdes, errdata, logger)
                if raise_exp:
                    raise e
            except Exception as e:
                _log_error(e, str(e), errdata, logger)
                if raise_exp:
                    raise e
            return res

        return new_func
    return decorator
