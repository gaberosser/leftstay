from leftstay import celery_app, utils
import models
import getter
import minion
import consts
from outcodes import OUTCODES
from random import shuffle
from leftstay.settings import DEFAULT_USER_AGENT, MINIMUM_ELAPSED_TIME_BEFORE_UPDATE_HR, URL_CHUNKSIZE
from django.utils import timezone


@celery_app.task(ignore_result=True)
def update_residential_property_for_sale_one_outcode(outcode_int, find_url, user_agent=DEFAULT_USER_AGENT):
    requester = getter.Requester(user_agent=user_agent)
    getter.update_one_outcode(outcode_int, find_url=find_url, requester=requester)


@celery_app.task(ignore_result=True)
def update_residential_property_for_sale(user_agent=DEFAULT_USER_AGENT):
    ## FIXME: would be nicer to have a shared global requester but can't JSON serialise the current Requester
    find_url = consts.FIND_URL_RESIDENTIAL_PROPERTY_FOR_SALE
    for d in OUTCODES:
        update_residential_property_for_sale_one_outcode.delay(d['code'], find_url, user_agent=user_agent)
