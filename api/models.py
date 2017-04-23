from django.contrib.gis.db import models
import consts


class PropertyForSaleSitemap(models.Model):
    url = models.URLField(null=False, blank=False, unique=True)
    accessed = models.DateTimeField(help_text="Timestamp for access", auto_created=True)
    status_code = models.IntegerField()
    last_modified = models.DateField(help_text="Last modified date according to the sitemap XML")
    content = models.TextField()


class KeyFeature(models.Model):
    property_for_sale = models.ForeignKey('api.PropertyForSale')
    feature = models.CharField(max_length=256)


class ListingHistory(models.Model):
    property_for_sale = models.ForeignKey('api.PropertyForSale')
    date = models.DateField()
    action = models.CharField(max_length=128)


class NearestStation(models.Model):
    property_for_sale = models.ForeignKey('api.PropertyForSale')
    distance_mi = models.FloatField()
    station = models.CharField(max_length=64)
    national_rail = models.BooleanField(default=False)
    tram = models.BooleanField(default=False)
    underground = models.BooleanField(default=False)
    overground = models.BooleanField(default=False)


class PropertyForSale(models.Model):
    url = models.URLField(null=False, blank=False)
    accessed = models.DateTimeField(help_text="Timestamp for access", auto_created=True)
    status_code = models.IntegerField()
    n_bed = models.IntegerField()
    asking_price = models.IntegerField()
    building_type = models.IntegerField(choices=consts.BUILDING_TYPE_CHOICES)
    key_features = models.TextField()
    full_description = models.TextField()
    agent_name = models.CharField(max_length=256)
    agent_address = models.CharField(max_length=256)
    agent_tel = models.CharField(max_length=20)
    location = models.PointField(srid=4326)