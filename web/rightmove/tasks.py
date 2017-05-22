from leftstay import celery_app, utils
import models
import getter
import minion
import consts
from leftstay.settings import DEFAULT_USER_AGENT, MINIMUM_ELAPSED_TIME_BEFORE_UPDATE_HR, URL_CHUNKSIZE
from django.utils import timezone


def update_one_chunk(user_agent, model, url_qset, **kwargs):
    minion = model(url_qset, user_agent, **kwargs)


@celery_app.task(ignore_result=True)
def update_one_chunk_property_for_sale(user_agent, ids, **kwargs):
    this_qset = models.PropertyUrl.objects.filter(id__in=ids)
    update_one_chunk(user_agent, minion.ResidentialForSaleMinion, this_qset, **kwargs)


@celery_app.task(ignore_result=True)
def update_property_urls(user_agent=DEFAULT_USER_AGENT):
    getter.update_property_sitemaps(user_agent=user_agent)
    getter.update_property_urls()


@celery_app.task(ignore_result=True)
def update_all_residential_for_sale(user_agent=DEFAULT_USER_AGENT, limit=None):
    tc = timezone.now() - timezone.timedelta(hours=MINIMUM_ELAPSED_TIME_BEFORE_UPDATE_HR)

    # get all URLs
    # the order here is equivalent to priority
    # Add NEW URLs first, then existing URLs in order of last access time

    new_ids = models.PropertyUrl.objects.filter(
        property_type=consts.PROPERTY_TYPE_FORSALE,
        deactivated__isnull=True,
        last_accessed__isnull=True
    ).values_list('id', flat=True)
    existing_ids = models.PropertyUrl.objects.filter(
        property_type=consts.PROPERTY_TYPE_FORSALE,
        deactivated__isnull=True,
        last_accessed__lt=tc
    ).order_by('last_accessed').values_list('id', flat=True)

    all_ids = list(new_ids) + list(existing_ids)
    if limit is not None:
        all_ids = all_ids[:limit]

    for ch in utils.chunk(all_ids, URL_CHUNKSIZE):
        update_one_chunk_property_for_sale.delay(user_agent, ch)
