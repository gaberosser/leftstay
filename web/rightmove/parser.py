# -*- coding: utf-8 -*-
from django.contrib.gis import geos
import datetime
from bs4 import BeautifulSoup, element
import re
import consts, models

NOT_PROPERTY = {
    'plot',
    'land',
    'block of apartments'
}

BUILDING_TYPE_MAP = {
    'studio flat': consts.BUILDING_TYPE_STUDIO_FLAT,
    'studio apartment': consts.BUILDING_TYPE_STUDIO_FLAT,
    'flat': consts.BUILDING_TYPE_FLAT,
    'apartment': consts.BUILDING_TYPE_FLAT,
    'maisonette': consts.BUILDING_TYPE_MAISONETTE,
    'house': consts.BUILDING_TYPE_HOUSE,
    'retirement property': consts.BUILDING_TYPE_RETIREMENT,
    'town house': consts.BUILDING_TYPE_TOWNHOUSE,
    'country house': consts.BUILDING_TYPE_COUNTRYHOUSE,
    'bungalow': consts.BUILDING_TYPE_BUNGALOW,
    'penthouse': consts.BUILDING_TYPE_PENTHOUSE,
}


BUILDING_SITUATION_MAP = {
    "detached": consts.BUILDING_SITUATION_DETACHED,
    "semi-detached": consts.BUILDING_SITUATION_SEMIDETACHED,
    "end of terrace": consts.BUILDING_SITUATION_ENDTERRACE,
    "terraced": consts.BUILDING_SITUATION_MIDTERRACE,
    "link detached": consts.BUILDING_SITUATION_LINKDETACHED,
    "ground floor": consts.BUILDING_SITUATION_GROUNDFLOOR,
}

STATION_TYPE_MAP = {
    "icon-national-train-station": consts.STATION_TYPE_NATIONAL_RAIL,
    "icon-tram-station": consts.STATION_TYPE_TRAM,
    "icon-london-underground": consts.STATION_TYPE_UNDERGROUND,
    "icon-london-overground": consts.STATION_TYPE_OVERGROUND,
}

removed_re = re.compile(r'This property has been removed by the agent', flags=re.I)
situation_re = re.compile("(?P<t>%s)" % "|".join(BUILDING_SITUATION_MAP.keys()), flags=re.I)
type_re = re.compile("(?P<t>%s)" % "|".join(BUILDING_TYPE_MAP.keys()), flags=re.I)
latlng_re = re.compile(r"latitude=(?P<lat>[-0-9\.]*).*longitude=(?P<lng>[-0-9\.]*)")


def residential_property_for_sale(src, url_obj=None):
    """
    :param src: Contains the raw text source for the property.
    :param url_obj: Optional. If supplied, this is used to set the required URL FK in the attributes. If not, this
    attribute MUST be set elsewhere before the deferred object can be saved.
    :returns: Dictionary with the following entries
        `errors`: dict of errors
        `deferred`: list of DeferredModel instances
        `status`: string with status or None
    """

    errors = {}
    deferred_objs = []
    status = None

    attrs = {'property_type': consts.PROPERTY_TYPE_FORSALE}

    if url_obj is not None:
        attrs['url_id'] = url_obj.id

    soup = BeautifulSoup(src, "html.parser")

    # has the property been removed?
    rem = soup.find(text=removed_re)
    if rem is not None:
        status = 'removed'

    # agent details

    x = soup.find(attrs={'class': 'agent-details-agent-logo'})
    agent_addr = x.find('address')
    if agent_addr:
        attrs['agent_address'] = agent_addr.text

    agent_name = x.find('strong')
    if agent_name:
        attrs['agent_name'] = agent_name.text

    agent_tel = x.find('a', attrs={'class': 'branch-telephone-number'})
    if agent_tel:
        attrs['agent_tel'] = agent_tel.text.strip('\n')

    # header attributes

    x = soup.find(attrs={'class': 'property-header-bedroom-and-price'})
    desc = x.find('h1')

    if desc is None:
        # without description, we won't have enough to go on
        errors['FAILED'] = True
        errors['failure_reason'] = 'No description found'
        errors['raw'] = src
        return {'errors': errors}

    desc = desc.text

    if re.search('retirement', desc):
        attrs['is_retirement'] = True

    # n beds if available

    nbeds = re.search(r'(?P<beds>[1-9]*)', desc)
    if nbeds is not None and nbeds != '':
        nbeds = nbeds.group('beds')
        try:
            attrs['n_bed'] = int(nbeds)
        except ValueError:
            pass

    prop = re.sub(' for sale.*$', '', desc)
    prop = re.sub('[1-9]* bedroom *', '', prop)

    if re.search('studio', prop, flags=re.I):
        attrs['n_bed'] = 1

    # we now seek to extract up to two elements: situation (e.g. 'detached') and type (e.g. penthouse)
    # the second is guaranteed, the first is optional

    sit = re.search(situation_re, prop)
    if sit:
        t = sit.group('t').lower()
        if t in BUILDING_SITUATION_MAP:
            attrs['building_situation'] = BUILDING_SITUATION_MAP[t]
        else:
            errors['building_situation'] = t
        prop2 = re.sub(situation_re, "", prop).strip()
    else:
        prop2 = prop

    typ = re.search(type_re, prop2)
    if typ:
        t = typ.group('t').lower()
        if t in BUILDING_TYPE_MAP:
            attrs['building_type'] = BUILDING_TYPE_MAP[t]
            if attrs['building_type'] == consts.BUILDING_TYPE_FLAT:
                attrs['building_situation'] = consts.BUILDING_SITUATION_FLAT
        else:
            errors['building_type'] = t
    else:
        errors['building_type'] = prop

    # description
    kf = soup.find(attrs={'class': 'key-features'})
    if kf is None:
        errors['key_features'] = 'not found'
    else:
        attrs['key_features'] = ';'.join([t.text for t in kf.find_all('li')])

    tenu = soup.find('span', attrs={'id': 'tenureType'})
    if tenu is not None:
        attrs['tenure_type'] = tenu.text

    # this is a mess, check whether it's robust

    desc = soup.find(attrs={'id': 'description'})
    a = desc.find(text='Full description')
    b = desc.find('h4', text='Listing History')
    if b is None:
        full_desc = [
            t.text.strip().strip('\r') for t in desc.contents if not isinstance(t, element.NavigableString)
        ]
    else:
        b = b.parent.parent
        full_desc = []
        g = a.nextGenerator()
        t = g.next()
        while t != b:
            if isinstance(t, element.NavigableString):
                t = t.strip().strip('\r')
                if t:
                    full_desc.append(t)
            t = g.next()
    if len(full_desc):
        attrs['full_description'] = '\n'.join(full_desc)
    else:
        errors['full_description'] = desc


    # location
    adds = x.find('address')
    if adds is None:
        attrs.setdefault('errors', {})['address_string'] = 'not found'
    else:
        attrs['address_string'] = adds.text

    map_static = soup.find(attrs={'alt': 'Get map and local information'})
    if map_static is None:
        errors['location'] = 'not found'
    else:
        t = map_static.get('src')
        latlng = re.search(latlng_re, t)
        if latlng is None:
            attrs.setdefault('errors', {})['location'] = t
        else:
            try:
                lat = float(latlng.group('lat'))
                lng = float(latlng.group('lng'))
                attrs['location'] = geos.Point(lng, lat, srid=4326)
            except ValueError:
                errors['location'] = t

    # date added

    dl = soup.find(attrs={'id': 'firstListedDateValue'})
    if dl is None:
        errors['date_listed'] = 'not found'
    else:
        try:
            attrs['date_listed'] = datetime.datetime.strptime(dl.text, '%d %B %Y').date()
        except Exception:
            errors['date_listed'] = dl.text

    # asking price

    prc = soup.find(attrs={'class': 'property-header-price'})
    if prc is None:
        errors['asking_price'] = 'not found'
    else:
        price = re.search(u'£(?P<price>[0-9,]*)', prc.text).group('price')
        try:
            attrs['asking_price'] = int(price.replace(',', ''))
        except ValueError:
            errors['asking_price'] = price

    # status and qualifier
    # status should not be used if property has been removed

    stat = soup.find(attrs={'class': 'property-header-qualifier'})
    if stat is not None:
        attrs['qualifier'] = stat.text

    ps = soup.find(attrs={'class': 'propertystatus'})
    if ps is not None:
        attrs['status'] = ps.text.strip('\n')

    deferred_prop = models.DeferredModel(models.PropertyForSale, attrs=attrs)
    deferred_objs.append(deferred_prop)

    # nearest stations
    deferred_nearest_stations = []
    sl = soup.find('ul', attrs={'class': 'stations-list'})
    if sl is None:
        errors['nearest_stations'] = 'not found'
    else:
        for t in sl.find_all('li'):
            try:
                name, dist = t.text.strip('\n').split('\n')
                dist = float(re.search(r'\((?P<d>[0-9\.]*) mi\)', dist).group('d'))
                cl = t.i.get('class')[-1]
                typ = STATION_TYPE_MAP[cl]
                attrs = {
                    'station': name,
                    'station_type': typ,
                    'distance_mi': dist,
                }
                def_nst = models.DeferredModel(
                    models.NearestStation,
                    attrs=attrs,
                    dependencies={'property': deferred_prop}
                )
                deferred_nearest_stations.append(def_nst)
            except Exception:
                errors.setdefault('nearest_stations', []).append(t)

    # sort by station name
    deferred_nearest_stations = sorted(
        deferred_nearest_stations,
        key=lambda d: d.attrs['station']
    )
    deferred_objs.extend(deferred_nearest_stations)

    out = {
        'errors': errors,
        'deferred': deferred_objs,
        'status': status,
    }

    return out