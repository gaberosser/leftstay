import requests
import logging
import re
from xml.etree import ElementTree
import datetime
from django.utils import timezone
import models
import consts
from leftstay.settings import TRANSACTION_CHUNK_SIZE, DEFAULT_USER_AGENT
from leftstay.utils import chunk
from api.getter import Requester
logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r'.*co\.uk\/([a-z-]*)\/.*$')


def urls_from_xml_string(s, filt=None):
    et = ElementTree.fromstring(s)
    g = et.iterfind('*%s' % et[0][0].tag)
    if filt is None:
        links = [t.text for t in g]
    else:
        links = []
        for t in g:
            if filt in t.text:
                links.append(t.text)
    return links


def get_xml_urls_from_sitemap(parent_xml, last_mod=None, filt=None):
    prop_xml = {}
    for e in parent_xml:
        this_url = e[0].text
        if filt is not None:
            if not re.search(filt, this_url):
                continue
        lm = datetime.datetime.strptime(e[1].text, '%Y-%m-%d').date()
        if last_mod is not None:
            if lm <= last_mod:
                # skip this entry since it hasn't changed
                continue
        prop_xml[this_url] = {'lastmod': lm}
    return prop_xml


def url_type(url):
    s = re.sub(URL_REGEX, '\g<1>', url)
    return consts.PROPERTY_TYPE_MAP.get(s)


class SitemapXmlGetter(object):

    XML_URL_FILTER = None
    DETAIL_FILTER = None

    def __init__(self, user_agent=DEFAULT_USER_AGENT, force_update=False):
        self.logger = logging.getLogger("rightmove.%s" % self.__class__.__name__)
        self.requester = Requester(user_agent=user_agent)

        self.existing_urls = None

        self.sitemap_xml = None
        self.prop_xml = None
        self.links = None

        self.initialise(force_update=force_update)

    def initialise(self, force_update=False):
        self.retrieve_existing_urls()

        try:
            self.logger.info("Getting base sitemap.xml")
            self.get_base_sitemap_xml()
            self.logger.info("Parsing URLs in base sitemap.xml")
            self.get_base_sitemap_urls()
        except requests.RequestException:
            self.logger.warning("Failed. Estimating the XML links instead. Some of these will fail by design.")
            self.prop_xml = self.estimate_base_sitemap_urls()

        self.logger.info("Retrieving XML data.")
        self.get_sitemap_xmls(force_update=force_update)

    def retrieve_existing_urls(self):
        raise NotImplementedError

    def get_base_sitemap_xml(self):
        ret = self.requester.get('http://www.rightmove.co.uk/sitemap.xml')
        if ret.status_code != 200:
            raise requests.RequestException("Unable to get XML list")
        self.sitemap_xml = ElementTree.fromstring(ret.content)

    def get_base_sitemap_urls(self, sitemap=None, last_mod=None):
        if sitemap is None:
            sitemap = self.sitemap_xml
        if sitemap is None:
            raise AttributeError("Sitemap XML has not been set. Run get_base_sitemap_xml().")
        self.prop_xml = get_xml_urls_from_sitemap(sitemap, filt=self.XML_URL_FILTER)

    def estimate_base_sitemap_urls(self):
        """
        Required if the base sitemap.xml is not accessible
        """
        raise NotImplementedError

    def retrieve_existing_record(self, url):
        """
        Get an existing record from the DB.
        """
        raise NotImplementedError

    def update_existing(self, obj, attrs):
        """
        Update an existing record with (potentially) new data
        """
        raise NotImplementedError

    def create_new(self, url, attrs):
        """
        Create a new record without any content
        """
        raise NotImplementedError

    def get_sitemap_xmls(self, force_update=False):
        if self.prop_xml is None:
            raise AttributeError(
                "Sub-XML URLs are not defined. Run get_base_sitemap_urls() or estimate_base_sitemap_urls().")

        for url, attrs in self.prop_xml.items():
            if url in self.existing_urls:
                b_exist = True
                obj = self.retrieve_existing_record(url)
                if not force_update and obj.last_modified >= attrs['lastmod']:
                    self.logger.info("XML sitemap at %s is unchanged.", url)
                    # use stored data
                    attrs['content'] = obj.content
                    attrs['status_code'] = obj.status_code
                    continue
                self.update_existing(obj, attrs)
            else:
                b_exist = False
                obj = self.create_new(url, attrs)

            self.logger.info("Getting XML sitemap at %s.", url)
            ret = self.requester.get(url)
            attrs['content'] = ret.content
            attrs['status_code'] = ret.status_code
            if ret.status_code != 200:
                self.logger.warning("Failed to get XML file: %s", url)
                # make an update anyway if the entry doesn't exist
                if not b_exist:
                    obj.status_code = ret.status_code
                    obj.content = ret.content
                    obj.accessed = timezone.now()
                    obj.save()
            else:
                obj.status_code = ret.status_code
                obj.content = ret.content
                obj.accessed = timezone.now()
                # set flag to ensure URLs are created/updated
                obj.urls_created = False
                obj.save()

    # def update_property_urls(self):
    #     if self.prop_xml is None:
    #         raise AttributeError(
    #             "Sub-XML URLs are not defined. Run get_base_sitemap_urls() or estimate_base_sitemap_urls().")
    #     self.links = []
    #     for url, attrs in self.prop_xml.iteritems():
    #         if attrs['status_code'] == 200:
    #             self.links.extend(urls_from_xml_string(attrs['content'], filt=self.DETAIL_FILTER))


class PropertyXmlGetter(SitemapXmlGetter):
    XML_URL_FILTER = 'propertydetails'
    DETAIL_FILTER = None

    def estimate_base_sitemap_urls(self):
        """
        Required if the base sitemap.xml is not accessible
        """
        urls = ['http://www.rightmove.co.uk/sitemap_propertydetails%d.xml' % i for i in range(1, 27)]
        lm = {'lastmod': datetime.date.today()}
        return dict([(t, dict(lm)) for t in urls])

    def retrieve_existing_urls(self):
        # only look up good results
        self.existing_urls = set(models.PropertySitemap.objects.filter(status_code=200).values_list('url', flat=True))

    def retrieve_existing_record(self, url):
        """
        Get an existing record from the DB.
        """
        return models.PropertySitemap.objects.get(url=url)

    def update_existing(self, obj, attrs):
        """
        Update an existing record with (potentially) new data
        """
        obj.last_modified = attrs['lastmod']

    def create_new(self, url, attrs):
        """
        Create a new record
        """
        return models.PropertySitemap(
            url=url,
            last_modified=attrs['lastmod'],
        )


def update_property_sitemaps(**kwargs):
    """
    Update the property sitemaps.
    Suspect that calling it this way might result in nicer garbage collection?
    """
    PropertyXmlGetter(**kwargs)


def url_generator(existing_urls):
    """
    Generator that returns unsaved PropertyUrl objects
    :param existing_urls: A set of URLs that already exist. **This is modified in place** to reflect the progress
    in an outer process. Horrid? Yes. Useful? Yes.
    """
    xml_to_update = models.PropertySitemap.objects.filter(urls_created=False, status_code=200).iterator()

    for x in xml_to_update:
        try:
            et = ElementTree.fromstring(x.content)
            g = et.iterfind('*%s' % et[0][0].tag)
            for el in g:
                t = el.text
                if t in existing_urls:
                    existing_urls.remove(t)
                else:
                    the_type = url_type(t)
                    obj = models.PropertyUrl(
                        url=t,
                        property_type=the_type,
                        created=timezone.now(),
                    )
                    yield obj
        except Exception:
            logger.exception("Failed to parse URLs from XML %s", x.url)


def update_property_urls():
    remaining = set(models.PropertyUrl.objects.filter(deactivated__isnull=True).values_list('url', flat=True))
    g = url_generator(remaining)
    # create in blocks
    create_count = 0

    for ch in chunk(g, TRANSACTION_CHUNK_SIZE):
        create_count += len(ch)
        logger.info("Creating block of %d records. Total created = %d.", len(ch), create_count)
        try:
            models.PropertyUrl.objects.bulk_create(ch)
        except Exception:
            logger.exception("Failed to create block")

    # infer that the remaining URLs have been removed
    logger.info("Deactivating %d URLs that were not found in the latest sitemaps.", len(remaining))
    models.PropertyUrl.objects.filter(url__in=remaining).update(deactivated=timezone.now())
