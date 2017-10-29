from leftstay import celery_app, utils
import models
import getter
import minion
import consts
from outcodes import OUTCODES
from leftstay.settings import DEFAULT_USER_AGENT, MINIMUM_ELAPSED_TIME_BEFORE_UPDATE_HR, URL_CHUNKSIZE
from django.utils import timezone


@celery_app.task(ignore_result=True)
def update_one_outcode(outcode_int, property_type, user_agent=DEFAULT_USER_AGENT):
    requester = getter.Requester(user_agent=user_agent)
    getter.update_one_outcode(outcode_int, property_type=property_type, requester=requester)


@celery_app.task(ignore_result=True)
def update_residential_property_for_sale(user_agent=DEFAULT_USER_AGENT):
    property_type = consts.PROPERTY_TYPE_FORSALE
    for d in OUTCODES:
        update_one_outcode.delay(d['code'], property_type, user_agent=user_agent)


@celery_app.task(ignore_result=True)
def update_residential_property_to_rent(user_agent=DEFAULT_USER_AGENT):
    property_type = consts.PROPERTY_TYPE_TORENT
    for d in OUTCODES:
        update_one_outcode.delay(d['code'], property_type, user_agent=user_agent)
