from bs4 import BeautifulSoup
import re
import consts

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
    'house': consts.BUILDING_TYPE_MAISONETTE,
    'retirement property': consts.BUILDING_TYPE_RETIREMENT,
    'town house': consts.BUILDING_TYPE_TOWNHOUSE,
    'country house': consts.BUILDING_TYPE_COUNTRYHOUSE,
    'bungalow': consts.BUILDING_TYPE_BUNGALOW,
    'penthouse': consts.BUILDING_TYPE_PENTHOUSE,
}

BUILDING_SITUATION_MAP = dict([
    (v.lower(), k) for k, v in dict(consts.BUILDING_SITUATION_CHOICES).items()
])

situation_re = re.compile("(?P<t>%s)" % "|".join(BUILDING_SITUATION_MAP.keys()), flags=re.I)
type_re = re.compile("(?P<t>%s)" % "|".join(BUILDING_TYPE_MAP.keys()), flags=re.I)

def residential_property_for_sale(src):
    # filter out unwanted items here

    res = {'property_type': consts.PROPERTY_TYPE_FORSALE}
    soup = BeautifulSoup(src, "html.parser")

    # agent details

    x = soup.find(attrs={'class': 'agent-details-agent-logo'})
    agent_addr = x.find('address')
    if agent_addr:
        res['agent_address'] = agent_addr.text

    agent_name = x.find('strong')
    if agent_name:
        res['agent_name'] = agent_name.text

    agent_tel = x.find('a', attrs={'class': 'branch-telephone-number'})
    if agent_tel:
        res['agent_tel'] = agent_tel.text

    # attributes
    x = soup.find(attrs={'class': 'property-header-bedroom-and-price'})
    desc = x.h1

    if desc is None:
        # without description, we won't have enough to go on
        res['FAILED'] = True
        res['failure_reason'] = 'No description found'
        res['raw'] = src
        return res

    desc = desc.text

    if re.search('retirement', desc):
        res['is_retirement'] = True

    # n beds if available
    nbeds = re.search(r'(?P<beds>[1-9]*)', desc)
    if nbeds is not None and nbeds != '':
        nbeds = nbeds.group('beds')
        try:
            res['nbeds'] = int(nbeds)
        except ValueError:
            pass

    prop = re.sub(' for sale.*$', '', desc)
    prop = re.sub('[1-9]* bedroom *', '', prop)

    # we now seek to extract up to two elements: situation (e.g. 'detached') and type (e.g. penthouse)
    # the second is guaranteed, the first is optional

    









    # description
    # location