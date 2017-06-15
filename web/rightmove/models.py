from django.contrib.gis.db import models
from django.utils import timezone
import logging
import consts

logger = logging.getLogger(__name__)

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
    outcode = models.IntegerField(help_text="Rightmove integer outcode", null=True, blank=True)
    postcode_outcode = models.CharField(help_text="First part of the postcode", max_length=4, null=True, blank=True)

    created = models.DateTimeField(help_text="Timestamp for creation", auto_created=True)
    deactivated = models.DateTimeField(help_text="Timestamp for deactivation", null=True)

    last_seen = models.DateTimeField(help_text="Timestamp for previous discovery", auto_created=True, null=True)
    last_accessed = models.DateTimeField(help_text="Timestamp for previous access", null=True)
    last_updated = models.DateTimeField(help_text="Timestamp for previous update", null=True)
    last_status_code = models.IntegerField(help_text="Status code obtained on previous update", null=True)

    consecutive_failed_attempts = models.IntegerField(default=0)


class DeferredModel(object):
    """
    Deferred classes hold attributes that _will_ be made into Django model objects later.
    Most of these attributes are held in `attributes`, however some models have dependencies on others
    (FK relationships) and cannot be created without them. This class allows us to defer saving until all dependencies
    have been satisfied and to ensure IDs are tracked correctly.
    :param dependencies: Dictionary. Keys are the model field name, values are other Deferred instances.
    """

    def __init__(self, model, attrs=None, dependencies=None):
        self.model = model
        self.attrs = attrs or {}
        self.dependencies = dependencies
        self.djobj = None

    @property
    def saved(self):
        return self.djobj is not None

    @property
    def dependencies_satisfied(self):
        if self.dependencies is None:
            return True
        for d in self.dependencies.values():
            if not d.saved:
                return False
        return True

    def save_dependencies(self, **kwargs):
        """
        Attempt to save all listed dependencies
        :param kwargs: Passed to Django model .save() method
        """
        if not self.dependencies_satisfied:
            for k, d in self.dependencies.items():
                if not d.saved:
                    try:
                        d.save(**kwargs)
                    except Exception:
                        logger.exception("Failed to save dependency %s", k)
                        raise

    def save(self, **kwargs):
        """
        :param kwargs: Passed to Django model .save() method
        """
        if self.saved:
            return

        self.save_dependencies(**kwargs)

        obj = self.model(**self.attrs)
        if self.dependencies is not None:
            for k, d in self.dependencies.items():
                setattr(obj, k, d.djobj)
        obj.save(**kwargs)
        obj.refresh_from_db()
        self.djobj = obj


class PropertySerializerMixin(object):

    def to_deferred(self):
        # check cache in case we have already created this object
        if hasattr(self, '_deferred'):
            return self._deferred
        attrs = self.get_attributes()
        deps = self.get_dependencies()
        self._deferred = DeferredModel(
            self.__class__,
            attrs=attrs,
            dependencies=deps
        )
        return self._deferred

    def get_dependencies(self):
        """
        Must be implemented in derived classes if required
        """
        return

    def get_attributes(self):
        excl = set(getattr(self, 'exclusions', []))
        fields = [f.name for f in self._meta.fields if f.name not in excl]
        res = dict([
            (f, getattr(self, f)) for f in fields
        ])
        return res

    @classmethod
    def from_deferred(cls, deferred):
        if not deferred.saved:
            deferred.save()
        return deferred.djobj


class NearestStation(models.Model, PropertySerializerMixin):
    exclusions = ['id', 'property']
    property = models.ForeignKey('PropertyBase')
    distance_mi = models.FloatField()
    station = models.CharField(max_length=64)
    station_type = models.IntegerField(choices=consts.STATION_TYPE_CHOICES)

    def get_dependencies(self):
        return {
            'property': self.property.to_deferred()
        }


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

    agent_name = models.CharField(max_length=256, null=True, blank=True)
    agent_address = models.CharField(max_length=256, null=True, blank=True)
    agent_tel = models.CharField(max_length=20, null=True, blank=True)

    location = models.PointField(srid=4326)
    address_string = models.CharField(max_length=256)

    qualifier = models.CharField(max_length=64)
    status = models.CharField(max_length=32, null=True, blank=True)

    def get_attributes(self):
        attrs = super(PropertyBase, self).get_attributes()
        attrs['url_id'] = self.url.id

    def save(self, **kwargs):
        if self.accessed is None:
            self.accessed = timezone.now()
        super(PropertyBase, self).save(**kwargs)


class PropertyForSale(PropertyBase):
    exclusions = PropertyBase.exclusions
    is_retirement = models.BooleanField(default=False)
    n_bed = models.IntegerField(null=True, blank=True)
    asking_price = models.IntegerField()
    price_on_application = models.BooleanField(default=False)
    building_type = models.IntegerField(choices=consts.BUILDING_TYPE_CHOICES)
    building_situation = models.IntegerField(choices=consts.BUILDING_SITUATION_CHOICES, null=True, blank=True)
    tenure_type = models.CharField(max_length=32, null=True, blank=True)
