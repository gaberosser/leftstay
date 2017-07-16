import requests
import logging
import re
from xml.etree import ElementTree
import datetime
from django.utils import timezone
from django.db import IntegrityError
import models
import consts
from outcodes import OUTCODE_MAP
import parser
from leftstay.settings import TRANSACTION_CHUNK_SIZE, DEFAULT_USER_AGENT
from leftstay.utils import chunk, dict_equality
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


def outcode_search_payload(outcode_int, index=None, per_page=48, include_sstc=True):
    """
    :param index: If supplied, this is the pagination parameter. This allows recursive calling.
    """
    outcode = "OUTCODE^%d" % outcode_int
    payload = {
        'locationIdentifier': outcode,
        'numberOfPropertiesPerPage': per_page,
        'viewType': 'LIST',
        'includeSSTC': 'true' if include_sstc else 'false',
    }
    if index is not None:
        payload['index'] = index

    return payload


def run_outcode_search(outcode_int, find_url, requester, payload):
    resp = requester.get(find_url, params=payload)
    if resp.status_code != 200:
        raise AttributeError("Failed to get links for outcode %d at URL %s. Error: %s" % (
            outcode_int, find_url, resp.content
        ))

    soup = BeautifulSoup(resp.content, "html.parser")
    dat = parser.parse_search_results(soup)
    nres = int(dat['pagination']['last'].strip().replace(',', ''))
    return soup, nres


def outcode_search_generator(outcode_int, find_url, requester=None, per_page=48):
    """
    :param index: If supplied, this is the pagination parameter. This allows recursive calling.
    """
    if requester is None:
        requester = requests
    payload = outcode_search_payload(outcode_int, per_page=per_page)
    soup, nres = run_outcode_search(outcode_int, find_url, requester, payload)

    indexes = range(per_page, nres + 1, per_page)  # add one to include final page
    yield soup
    for i in indexes:
        payload = outcode_search_payload(outcode_int, per_page=per_page, index=i)
        try:
            soup, nres = run_outcode_search(outcode_int, find_url, requester, payload)
            yield soup
        except Exception:
            logger.exception("Failed to get page of results with index %d", i)


def update_one_outcode(outcode_int, property_type, requester=None):
    """
    """
    find_url = consts.FIND_URLS[property_type]
    pc_code = OUTCODE_MAP[outcode_int]
    parse = None
    if property_type == consts.PROPERTY_TYPE_FORSALE:
        parse = parser.residential_property_for_sale_from_search
    else:
        raise NotImplementedError
    # get all known URLs
    url_dict = dict([
        (x.url, x) for x in models.PropertyUrl.objects.filter(postcode_outcode=pc_code)
            .prefetch_related('property_set')
    ])

    for i, soup in enumerate(outcode_search_generator(outcode_int, find_url, requester=requester)):
        res, errors = parse(soup)

        if len(errors):
            logger.error(
                "%d errors raised from page %d of outcode %d",
                len(errors), i + 1, outcode_int
            )
            # TODO: this might be large
            logger.error(repr(errors))
        for url, d in res:
            try:
                # we have to set the property type and model here
                if url in url_dict:
                    url_obj = url_dict.pop(url)
                    if url_obj.property_set.exists():
                        most_recent = url_obj.property_set.latest('accessed').to_deferred()
                        eq = dict_equality(d.attrs, most_recent.attrs, return_diff=False)
                        to_update = not eq
                    else:
                        to_update = True
                else:
                    to_update = True
                    url_obj = models.PropertyUrl(
                        created=timezone.now(),
                        url=url,
                        property_type=property_type,
                        outcode=outcode_int,
                        postcode_outcode=pc_code,
                        last_seen=timezone.now(),
                    )
                    try:
                        url_obj.save()
                    except IntegrityError:
                        # try to help track down why this error occurs
                        # FIXME: I think these are OVERLAPPING entries, so the object isn't in url_dict to begin with
                        # SOLUTION: have a second dict to keep track of those added?
                        logger.exception("Failed to save URL object because the URL is already stored."
                                         "Outcode %d, postcode %s, url %s with ID %s.",
                                         outcode_int, pc_code, url, str(url_obj.id),
                                         )
                # set the URL FK link
                if to_update:
                    url_def = url_obj.to_deferred()
                    d.dependencies['url'] = url_def
                    d.save()
                    url_obj.last_updated = timezone.now()
                    url_obj.save()

            except Exception:
                logger.exception("Failed to update URL %s in postcode %s", url, pc_code)

    to_deactivate = models.PropertyUrl.objects.exclude(
        url__in=url_dict.keys()
    )
    try:
        to_deactivate.update(deactivated=timezone.now(), outcode=outcode_int, postcode_outcode=pc_code)
    except Exception:
        logger.exception("Failed to deactivate %d records for outcode %d", len(to_deactivate), outcode_int)
