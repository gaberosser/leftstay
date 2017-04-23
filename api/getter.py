import requests
import logging
import re
from xml.etree import ElementTree
import datetime
import models


def urls_from_xml_string(s, filt=None):
    links = []
    et = ElementTree.fromstring(s)
    for t in et:
        if filt is not None:
            if filt not in t[0].text:
                continue
        links.append(t[0].text)
    return links


def get_xml_urls_from_sitemap(parent_xml, last_mod=None, filt=None):
    prop_xml = {}
    for e in parent_xml:
        this_url = e[0].text
        if filt is not None:
            if not re.search(filt, this_url):
                continue
        lm = datetime.datetime.strptime(e[1].text, '%Y-%m-%d').date
        if last_mod is not None:
            if lm <= last_mod:
                # skip this entry since it hasn't changed
                continue
        prop_xml[this_url] = {'lastmod': lm}
    return prop_xml


class PropertyConnector(object):

    XML_URL_FILTER = None
    DETAIL_FILTER = None

    def __init__(self, force_update=False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.handlers = []
        self.logger.addHandler(logging.StreamHandler())
        self.logger.setLevel(logging.DEBUG)

        self.existing_records = None

        self.sitemap_xml = None
        self.prop_xml = None
        self.links = None

        self.initialise(force_update=force_update)

    def initialise(self, force_update=False):
        self.retrieve_existing_records()

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
        self.logger.info("Parsing detailed links in XML data")
        self.get_detailed_links()

    def retrieve_existing_records(self):
        raise NotImplementedError

    def get_base_sitemap_xml(self):
        ret = requests.get('http://www.rightmove.co.uk/sitemap.xml')
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

    def get_sitemap_xmls(self, force_update=False):
        if self.prop_xml is None:
            raise AttributeError(
                "Sub-XML URLs are not defined. Run get_base_sitemap_urls() or estimate_base_sitemap_urls().")

        for url, attrs in self.prop_xml.items():
            if url in self.existing_records:
                b_exist = True
                obj = self.existing_records[url]
                print attrs
                if not force_update and self.existing_records[url].last_modified >= attrs['lastmod']:
                    self.logger.info("XML sitemap at %s is unchanged.", url)
                    # use stored data
                    attrs['content'] = self.existing_records[url].content
                    attrs['status_code'] = self.existing_records[url].status_code
                    continue
                obj.last_modified = attrs['lastmod']
            else:
                b_exist = False
                obj = models.PropertyForSaleSitemap(
                    url=url,
                    last_modified=attrs['lastmod'],
                )

            self.logger.info("Getting XML sitemap at %s.", url)
            ret = requests.get(url)
            attrs['content'] = ret.content
            attrs['status_code'] = ret.status_code
            if ret.status_code != 200:
                self.logger.warning("Failed to get XML file: %s", url)
                # make an update anyway if the entry doesn't exist
                if not b_exist:
                    obj.status_code = ret.status_code
                    obj.content = ret.content
                    obj.accessed = datetime.datetime.now()
                    obj.save()
            else:
                obj.status_code = ret.status_code
                obj.content = ret.content
                obj.accessed = datetime.datetime.now()
                obj.save()

    def get_detailed_links(self):
        if self.prop_xml is None:
            raise AttributeError(
                "Sub-XML URLs are not defined. Run get_base_sitemap_urls() or estimate_base_sitemap_urls().")
        self.links = []
        for url, attrs in self.prop_xml.iteritems():
            if attrs['status_code'] == 200:
                self.links.extend(urls_from_xml_string(attrs['content'], filt=self.DETAIL_FILTER))

    def get_one(self, url, existing=None):
        pass


class PropertySales(PropertyConnector):
    XML_URL_FILTER = 'propertydetails'
    DETAIL_FILTER = '/property-for-sale/'

    def estimate_base_sitemap_urls(self):
        """
        Required if the base sitemap.xml is not accessible
        """
        urls = ['http://www.rightmove.co.uk/sitemap_propertydetails%d.xml' % i for i in range(1, 27)]
        lm = {'lastmod': datetime.date(1900, 1, 1)}
        return dict([(t, dict(lm)) for t in urls])

    def retrieve_existing_records(self):
        # only look up good results
        recs = models.PropertyForSaleSitemap.objects.filter(status_code=200)
        self.existing_records = dict([
            (t.url, t) for t in recs
        ])