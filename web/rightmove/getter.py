import requests
import logging
import re
from xml.etree import ElementTree
import datetime
from django.utils import timezone
import models
import consts
from outcodes import OUTCODE_MAP
from leftstay.settings import TRANSACTION_CHUNK_SIZE, DEFAULT_USER_AGENT
from leftstay.utils import chunk
from api.getter import Requester
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r'.*co\.uk\/([a-z-]*)\/.*$')


# def urls_from_xml_string(s, filt=None):
#     et = ElementTree.fromstring(s)
#     g = et.iterfind('*%s' % et[0][0].tag)
#     if filt is None:
#         links = [t.text for t in g]
#     else:
#         links = []
#         for t in g:
#             if filt in t.text:
#                 links.append(t.text)
#     return links


# def get_xml_urls_from_sitemap(parent_xml, last_mod=None, filt=None):
#     prop_xml = {}
#     for e in parent_xml:
#         this_url = e[0].text
#         if filt is not None:
#             if not re.search(filt, this_url):
#                 continue
#         lm = datetime.datetime.strptime(e[1].text, '%Y-%m-%d').date()
#         if last_mod is not None:
#             if lm <= last_mod:
#                 # skip this entry since it hasn't changed
#                 continue
#         prop_xml[this_url] = {'lastmod': lm}
#     return prop_xml


# def url_type(url):
#     s = re.sub(URL_REGEX, '\g<1>', url)
#     return consts.PROPERTY_TYPE_MAP.get(s)


# class SitemapXmlGetter(object):
#
#     XML_URL_FILTER = None
#     DETAIL_FILTER = None
#
#     def __init__(self, user_agent=DEFAULT_USER_AGENT, force_update=False):
#         self.logger = logging.getLogger("rightmove.%s" % self.__class__.__name__)
#         self.requester = Requester(user_agent=user_agent)
#
#         self.existing_urls = None
#
#         self.sitemap_xml = None
#         self.prop_xml = None
#         self.links = None
#
#         self.initialise(force_update=force_update)
#
#     def initialise(self, force_update=False):
#         self.retrieve_existing_urls()
#
#         try:
#             self.logger.info("Getting base sitemap.xml")
#             self.get_base_sitemap_xml()
#             self.logger.info("Parsing URLs in base sitemap.xml")
#             self.get_base_sitemap_urls()
#         except requests.RequestException:
#             self.logger.warning("Failed. Estimating the XML links instead. Some of these will fail by design.")
#             self.prop_xml = self.estimate_base_sitemap_urls()
#
#         self.logger.info("Retrieving XML data.")
#         self.get_sitemap_xmls(force_update=force_update)
#
#     def retrieve_existing_urls(self):
#         raise NotImplementedError
#
#     def get_base_sitemap_xml(self):
#         ret = self.requester.get('http://www.rightmove.co.uk/sitemap.xml')
#         if ret.status_code != 200:
#             raise requests.RequestException("Unable to get XML list")
#         self.sitemap_xml = ElementTree.fromstring(ret.content)
#
#     def get_base_sitemap_urls(self, sitemap=None, last_mod=None):
#         if sitemap is None:
#             sitemap = self.sitemap_xml
#         if sitemap is None:
#             raise AttributeError("Sitemap XML has not been set. Run get_base_sitemap_xml().")
#         self.prop_xml = get_xml_urls_from_sitemap(sitemap, filt=self.XML_URL_FILTER)
#
#     def estimate_base_sitemap_urls(self):
#         """
#         Required if the base sitemap.xml is not accessible
#         """
#         raise NotImplementedError
#
#     def retrieve_existing_record(self, url):
#         """
#         Get an existing record from the DB.
#         """
#         raise NotImplementedError
#
#     def update_existing(self, obj, attrs):
#         """
#         Update an existing record with (potentially) new data
#         """
#         raise NotImplementedError
#
#     def create_new(self, url, attrs):
#         """
#         Create a new record without any content
#         """
#         raise NotImplementedError
#
#     def get_sitemap_xmls(self, force_update=False):
#         if self.prop_xml is None:
#             raise AttributeError(
#                 "Sub-XML URLs are not defined. Run get_base_sitemap_urls() or estimate_base_sitemap_urls().")
#
#         for url, attrs in self.prop_xml.items():
#             if url in self.existing_urls:
#                 b_exist = True
#                 obj = self.retrieve_existing_record(url)
#                 if not force_update and obj.last_modified >= attrs['lastmod']:
#                     self.logger.info("XML sitemap at %s is unchanged.", url)
#                     # use stored data
#                     attrs['content'] = obj.content
#                     attrs['status_code'] = obj.status_code
#                     continue
#                 self.update_existing(obj, attrs)
#             else:
#                 b_exist = False
#                 obj = self.create_new(url, attrs)
#
#             self.logger.info("Getting XML sitemap at %s.", url)
#             ret = self.requester.get(url)
#             attrs['content'] = ret.content
#             attrs['status_code'] = ret.status_code
#             if ret.status_code != 200:
#                 self.logger.warning("Failed to get XML file: %s", url)
#                 # make an update anyway if the entry doesn't exist
#                 if not b_exist:
#                     obj.status_code = ret.status_code
#                     obj.content = ret.content
#                     obj.accessed = timezone.now()
#                     obj.save()
#             else:
#                 obj.status_code = ret.status_code
#                 obj.content = ret.content
#                 obj.accessed = timezone.now()
#                 # set flag to ensure URLs are created/updated
#                 obj.urls_created = False
#                 obj.save()


# class PropertyXmlGetter(SitemapXmlGetter):
#     XML_URL_FILTER = 'propertydetails'
#     DETAIL_FILTER = None
#
#     def estimate_base_sitemap_urls(self):
#         """
#         Required if the base sitemap.xml is not accessible
#         """
#         urls = ['http://www.rightmove.co.uk/sitemap_propertydetails%d.xml' % i for i in range(1, 27)]
#         lm = {'lastmod': datetime.date.today()}
#         return dict([(t, dict(lm)) for t in urls])
#
#     def retrieve_existing_urls(self):
#         # only look up good results
#         self.existing_urls = set(models.PropertySitemap.objects.filter(status_code=200).values_list('url', flat=True))
#
#     def retrieve_existing_record(self, url):
#         """
#         Get an existing record from the DB.
#         """
#         return models.PropertySitemap.objects.get(url=url)
#
#     def update_existing(self, obj, attrs):
#         """
#         Update an existing record with (potentially) new data
#         """
#         obj.last_modified = attrs['lastmod']
#
#     def create_new(self, url, attrs):
#         """
#         Create a new record
#         """
#         return models.PropertySitemap(
#             url=url,
#             last_modified=attrs['lastmod'],
#         )


def _links_from_search(soup, base_url):
    results = soup.find_all('a', attrs={'class': "propertyCard-headerLink"})
    urls = set()
    for el in results:
        par = el.parent.parent.parent
        if 'is-hidden' not in par['class']:
            urls.add(base_url + el['href'])
    return urls


def get_links_one_outcode(outcode_int, find_url, requester=None, per_page=48, index=None):
    """
    :param index: If supplied, this is the pagination parameter. This allows recursive calling.
    """
    outcode = "OUTCODE^%d" % outcode_int
    base_url = "http://www.rightmove.co.uk"
    if requester is None:
        requester = requests
    payload = {
        'locationIdentifier': outcode,
        'numberOfPropertiesPerPage': per_page,
        'viewType': 'LIST',
    }
    if index is not None:
        payload['index'] = index

    resp = requester.get(find_url, params=payload)
    if resp.status_code != 200:
        raise AttributeError("Failed to get links for outcode %s at URL %s. Error: %s" % (
            outcode, find_url, resp.content
        ))

    soup = BeautifulSoup(resp.content, "html.parser")

    if index is None:
        el = soup.find("span", attrs={'class': 'searchHeader-resultCount'})
        nres = int(el.text)
        indexes = range(per_page, nres, per_page)
        # pagination works by supplying an index parameter giving the number of the first link shown (zero indexed)
        # this first result is (obv) the first page. We can then call the function recursively for the remainder
        urls = _links_from_search(soup, base_url)
        for i in indexes:
            try:
                urls.update(get_links_one_outcode(
                    outcode_int,
                    find_url,
                    requester=requester,
                    per_page=per_page,
                    index=i
                ))
            except Exception:
                logger.exception("Failed to get URL results for outcode %s with index %d", outcode, i)
    else:
        urls = _links_from_search(soup, base_url)

    return urls


def outcode_search_generator(outcode_int, find_url, requester=None, per_page=48, index=None):
    ## FIXME: does this kind of recursive generator actually work??
    """
    :param index: If supplied, this is the pagination parameter. This allows recursive calling.
    """
    outcode = "OUTCODE^%d" % outcode_int
    if requester is None:
        requester = requests
    payload = {
        'locationIdentifier': outcode,
        'numberOfPropertiesPerPage': per_page,
        'viewType': 'LIST',
    }
    if index is not None:
        payload['index'] = index

    resp = requester.get(find_url, params=payload)
    if resp.status_code != 200:
        raise AttributeError("Failed to get links for outcode %s at URL %s. Error: %s" % (
            outcode, find_url, resp.content
        ))

    soup = BeautifulSoup(resp.content, "html.parser")

    if index is None:
        el = soup.find("span", attrs={'class': 'searchHeader-resultCount'})
        nres = int(el.text)
        indexes = range(per_page, nres, per_page)

        yield soup
        for i in indexes:
            try:
                yield outcode_search_generator(
                    outcode_int,
                    find_url,
                    requester=requester,
                    per_page=per_page,
                    index=i
                )
            except Exception:
                logger.exception("Failed to get URL results for outcode %s with index %d", outcode, i)
    else:
        yield soup



def update_one_outcode(outcode_int, find_url, requester=None):
    """
    TODO: rewrite this.
    Get the search data
    Parse the JSON
    Add/amend relevant Url and Property objects
    Iterate over pagination
    """


    try:
        urls = get_links_one_outcode(outcode_int, find_url=find_url, requester=requester)
    except Exception:
        logger.exception("Failed to get URLs for outcode %d at %s", outcode_int, find_url)
        raise

    pc_code = OUTCODE_MAP[outcode_int]

    # existing
    existing = set(models.PropertyUrl.objects.values_list('url', flat=True))

    # create
    to_create = set(urls).difference(existing)
    for ch in chunk(to_create, TRANSACTION_CHUNK_SIZE):
        objs = [
            models.PropertyUrl(
                url=u,
                property_type=url_type(u),
                created=timezone.now(),
                last_seen=timezone.now(),
                outcode=outcode_int,
                postcode_outcode=pc_code,
            ) for u in ch
        ]
        try:
            models.PropertyUrl.objects.bulk_create(objs)
        except Exception:
            logger.exception("Failed to create chunk for outcode %d", outcode_int)

    # update
    to_update = existing.intersection(urls)
    try:
        models.PropertyUrl.objects.filter(
            url__in=to_update
        ).update(last_seen=timezone.now(), outcode=outcode_int, postcode_outcode=pc_code, deactivated=None)
    except Exception:
        logger.exception("Failed to update %d records for outcode %d", len(to_update), outcode_int)


    # deactivate
    to_deactivate = models.PropertyUrl.objects.exclude(
        url__in=urls
    ).filter(
        outcode=outcode_int,
        deactivated__isnull=True,
    )
    try:
        to_deactivate.update(deactivated=timezone.now(), outcode=outcode_int, postcode_outcode=pc_code)
    except Exception:
        logger.exception("Failed to deactivate %d records for outcode %d", len(to_deactivate), outcode_int)
