# coding=UTF8
from __future__ import absolute_import

import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "leftstay.settings")

app = Celery('leftstay')

CELERY_TIMEZONE = 'UTC'

app.config_from_object(settings)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
