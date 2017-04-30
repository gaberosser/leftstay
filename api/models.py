from django.contrib.gis.db import models
import consts


class PropertySitemap(models.Model):
    """
    urls_created: If False, this is a flag specifying that we need to update the property URLs contained within.
    This field is then set to True to avoid unnecessary repetition.
    """
    url = models.URLField(null=False, blank=False, unique=True)
    accessed = models.DateTimeField(help_text="Timestamp for access", auto_created=True)
    status_code = models.IntegerField()
    last_modified = models.DateField(help_text="Last modified date according to the sitemap XML")
    content = models.TextField()
    urls_created = models.BooleanField(default=False, help_text="Have URLs been created/updated for this entry?")


class PropertyUrl(models.Model):
    """
    created: Datetime for URL creation
    last_accessed: Last datetime an attempt was made to access the URL
    last_updated:
    """
    url = models.URLField(null=False, blank=False, unique=True)
    property_type = models.IntegerField(choices=consts.PROPERTY_TYPE_CHOICES)
    last_known_status = models.IntegerField(choices=consts.URL_STATUS_CHOICES, null=True, blank=True)

    created = models.DateTimeField(help_text="Timestamp for creation", auto_created=True)
    deactivated = models.DateTimeField(help_text="Timestamp for deactivation", auto_created=True, null=True)

    last_accessed = models.DateTimeField(help_text="Timestamp for previous access", null=True)
    last_updated = models.DateTimeField(help_text="Timestamp for previous update", null=True)
    last_status_code = models.IntegerField(help_text="Status code obtained on previous update", null=True)


class PropertySerializerMixin(object):
    def to_dict(self):
        excl = set(getattr(self, 'exclusions', default=[]))
        fields = [f.name for f in self._meta.fields if f.name not in excl]
        res = dict([
            (f, getattr(self, f)) for f in fields
        ])
        return res

    @classmethod
    def from_dict(cls, x):
        x = dict(x)
        kwargs = {}
        excl = set(getattr(cls, 'exclusions', default=[]))
        for f in cls._meta.fields:
            if f in x and f.name not in excl:
                kwargs[f.name] = x[f.name]
        kwargs['url_id'] = x['url_id']
        return cls(**kwargs)


# class KeyFeature(models.Model, SerializerMixin):
#     property_for_sale = models.ForeignKey('PropertyBase')
#     feature = models.CharField(max_length=256)


# class ListingHistory(models.Model, PropertySerializerMixin):
#     property_for_sale = models.ForeignKey('PropertyBase')
#     date = models.DateField()
#     action = models.CharField(max_length=128)


class NearestStation(models.Model, PropertySerializerMixin):
    exclusions = ['id', 'property']
    property = models.ForeignKey('PropertyBase')
    distance_mi = models.FloatField()
    station = models.CharField(max_length=64)
    station_type = models.IntegerField(choices=consts.STATION_TYPE_CHOICES)

    def to_dict(self):
        res = super(NearestStation, self).to_dict()
        res['property_id'] = self.property.id
        return res

    def from_dict(cls, x):
        obj = super(NearestStation, cls).from_dict(x)
        obj.property_id = x['property_id']
        return obj


class PropertyBase(models.Model, PropertySerializerMixin):
    exclusions = [
        'id',
        'url',
        'propertybase_ptr',
    ]

    url = models.ForeignKey('PropertyUrl', null=False, blank=False)
    requester_id = models.CharField(max_length=32)
    
    accessed = models.DateTimeField(help_text="Timestamp for access", auto_created=True)

    date_listed = models.DateField(null=True, blank=True)
    property_type = models.IntegerField(choices=consts.PROPERTY_TYPE_CHOICES)
    key_features = models.TextField(null=True, blank=True)
    full_description = models.TextField(null=True, blank=True)

    agent_name = models.CharField(max_length=256)
    agent_address = models.CharField(max_length=256)
    agent_tel = models.CharField(max_length=20)

    location = models.PointField(srid=4326)
    address_string = models.CharField(max_length=256)

    qualifier = models.CharField(max_length=64)
    status = models.CharField(max_length=32, null=True, blank=True)


class PropertyForSale(PropertyBase):
    exclusions = PropertyBase.exclusions
    is_retirement = models.BooleanField(default=False)
    n_bed = models.IntegerField()
    asking_price = models.IntegerField()
    building_type = models.IntegerField(choices=consts.BUILDING_TYPE_CHOICES)
    building_situation = models.IntegerField(choices=consts.BUILDING_SITUATION_CHOICES)
    tenure_type = models.CharField(max_length=32, null=True, blank=True)

    def to_dict(self):
        res = super(PropertyForSale, self).to_dict()
        # add foreign key fields: nearest stations, key features?
        if self.neareststation_set.exists():
            res['nearest_station'] = [t.to_dict() for t in self.neareststation_set.all()]
        res['url_id'] = self.url.id
        return res

    def from_dict(cls, x):
        l = super(PropertyForSale, cls).from_dict(x)
        l.url_id = x['url_id']
        l = [l] + [NearestStation.from_dict(t) for t in x.get('nearest_station', [])]
        return l