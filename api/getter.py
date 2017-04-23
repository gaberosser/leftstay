import requests
import logging
import re
from xml.etree import ElementTree


def urls_from_xml_string(s, filter=None):
    links = []
    et = ElementTree.fromstring(s)
    for t in et:
        if filter is not None and filter in t[0].text:
            links.append(t[0].text)
        else:
            links.append(t[0].text)
    return links


class Connector(object):

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.addHandler(logging.StreamHandler())
        self.logger.setLevel(logging.DEBUG)

        self.sitemap_xml = None
        self.prop_xml = None
        self.property_links = None


    def get_sitemap_xml(self):
        ret = requests.get('http://www.rightmove.co.uk/sitemap.xml')
        if ret.status_code != 200:
            raise requests.RequestException("Unable to get XML list")
        self.sitemap_xml = ElementTree.fromstring(ret.content)

    def get_property_details_xml(self, sitemap=None):

        if sitemap is None:
            sitemap = self.sitemap_xml
        if sitemap is None:
            raise AttributeError("Sitemap XML has not been set. Run get_sitemap_xml().")

        prop_xml = {}
        links = []

        for e in sitemap:
            if re.search(r'propertydetails', e[0].text):
                prop_xml[e[0].text] = {'lastmod': e[1].text}

        self.prop_xml = prop_xml

    def get_property_sale_details_links(self, prop_xml=None):

        if prop_xml is None:
            prop_xml = self.prop_xml

        if prop_xml is None:
            raise AttributeError("Propert XML links have not been set. Run get_property_details_xml().")

        links = []

        for i, x in enumerate(prop_xml):
            self.logger.info("Getting links from %s", x)
            ret = requests.get(x)
            if ret.status_code == 200:
                links.extend(urls_from_xml_string(ret.content, 'property-for-sale'))
            else:
                # error handling
                print "Failed to get XML file: %s" % x
                pass

        self.property_links = links
