import requests
import logging
from functools import wraps
import datetime
from django.utils import timezone
import time
from django.conf import settings

REQUEST_FROM = getattr(settings, 'REQUEST_FROM', None)


def limited_requests(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        self.check_limits()
        resp = fn(self, *args, **kwargs)
        self.increment_call_counts()
        return resp
    return wrapper


def with_headers(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = self.headers
        return fn(self, *args, **kwargs)
    return wrapper


class Singleton(type):
    """
    Declare a singleton class by setting `__metaclass__ = Singleton`
    The effect is that `__call__` is called during instantiation, before `__init__`.
    If an instance already exists, we return that, so only one instance ever exists.
    """
    _instances = {}

    def __call__(cls, base_id=None, *args, **kwargs):
        # this gets called
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(base_id=base_id, *args, **kwargs)
        elif base_id is not None and base_id != cls._instances[cls].base_id:
            raise ValueError("Requested base ID does not match existing singleton instance (%s)." % cls._instances[cls].base_id)
        return cls._instances[cls]


class RequesterSingleton(object):
    __metaclass__ = Singleton
    LIMIT_PER_SEC = None
    LIMIT_PER_HR = None

    def __init__(self, base_id=None, headers=None):
        if base_id is None:
            base_id = "LeftStay-requester-base"
        self.base_id = base_id
        self._total_calls = 0
        self.calls_this_second = 0
        self.calls_this_hour = 0
        self.second_time = timezone.now()
        self.hour_time = timezone.now()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.headers = requests.utils.default_headers()
        if headers is not None:
            self.headers.update(headers)

    def increment_call_counts(self):
        now = timezone.now()
        self._total_calls += 1

        if (now - self.second_time).total_seconds() > 1:
            self.calls_this_second = 1
            self.second_time = now
        else:
            self.calls_this_second += 1

        if (now - self.hour_time).total_seconds() / 3600. > 1:
            self.calls_this_hour = 1
            self.hour_time = now
        else:
            self.calls_this_hour += 1

    def check_limits(self):
        """
        Test whether we have exceeded any limits and, if so, wait
        :return:
        """
        if self.LIMIT_PER_SEC is not None:
            if self.calls_this_second == self.LIMIT_PER_SEC:
                # wait until the second is up
                wait_til = self.second_time + datetime.timedelta(seconds=1)
                wait_for = (wait_til - timezone.now()).total_seconds()
                self.logger.info("Exceeded per second limit. Sleeping for %.2f seconds...", wait_for)
                time.sleep(wait_for)

        if self.LIMIT_PER_HR is not None:
            if self.calls_this_hour == self.LIMIT_PER_HR:
                # wait until the hour is up
                wait_til = self.hour_time + datetime.timedelta(hours=1)
                wait_for = (wait_til - timezone.now()).total_seconds()
                self.logger.info("Exceeded per hour limit. Sleeping for %d minutes...", int(wait_for / 60.))
                time.sleep(wait_for)

    @with_headers
    @limited_requests
    def get(self, url, params=None, **kwargs):
        resp = requests.get(url, params=params, **kwargs)
        return resp

    @with_headers
    @limited_requests
    def post(self, url, data=None, json=None, **kwargs):
        resp = requests.post(url, data=data, json=json, **kwargs)
        return resp


class Requester(object):
    def __init__(self, user_agent):
        self.user_agent = user_agent
        self.headers = {
            'User-Agent': self.user_agent,
        }
        if REQUEST_FROM is not None:
            self.headers['From'] = REQUEST_FROM
        self.requester = RequesterSingleton(headers=self.headers)

    def __getattr__(self, item):
        attr = getattr(self.requester, item, None)
        if attr is not None:
            return attr
        else:
            raise AttributeError
