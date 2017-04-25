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


class KeyFeature(models.Model):
    property_for_sale = models.ForeignKey('PropertyBase')
    feature = models.CharField(max_length=256)


class ListingHistory(models.Model):
    property_for_sale = models.ForeignKey('PropertyBase')
    date = models.DateField()
    action = models.CharField(max_length=128)


class NearestStation(models.Model):
    property_for_sale = models.ForeignKey('PropertyBase')
    distance_mi = models.FloatField()
    station = models.CharField(max_length=64)
    national_rail = models.BooleanField(default=False)
    tram = models.BooleanField(default=False)
    underground = models.BooleanField(default=False)
    overground = models.BooleanField(default=False)


class PropertyBase(models.Model):
    url = models.ForeignKey('PropertyUrl', null=False, blank=False)
    # url = models.URLField(null=False, blank=False)
    accessed = models.DateTimeField(help_text="Timestamp for access", auto_created=True)
    status_code = models.IntegerField()
    full_description = models.TextField()
    agent_name = models.CharField(max_length=256)
    agent_address = models.CharField(max_length=256)
    agent_tel = models.CharField(max_length=20)
    location = models.PointField(srid=4326)


class PropertyForSale(PropertyBase):
    # url = models.URLField(null=False, blank=False)
    # accessed = models.DateTimeField(help_text="Timestamp for access", auto_created=True)
    # status_code = models.IntegerField()
    n_bed = models.IntegerField()
    asking_price = models.IntegerField()
    building_type = models.IntegerField(choices=consts.BUILDING_TYPE_CHOICES)
    # full_description = models.TextField()
    # agent_name = models.CharField(max_length=256)
    # agent_address = models.CharField(max_length=256)
    # agent_tel = models.CharField(max_length=20)
    # location = models.PointField(srid=4326)