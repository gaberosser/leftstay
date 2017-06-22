from django.contrib.gis.db import models


class Author(models.Model):
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    make_bold = models.BooleanField(default=False)


class Publication(models.Model):
    title = models.TextField()
    authors = models.ManyToManyField(Author)
    year = models.IntegerField()
    journal = models.TextField()
    volume = models.CharField(max_length=8, null=True, blank=True)
    edition = models.CharField(max_length=8, null=True, blank=True)
    page_start = models.CharField(max_length=8, null=True, blank=True)
    page_end = models.CharField(max_length=8, null=True, blank=True)


class Presentation(models.Model):
    title = models.TextField()
    authors = models.ManyToManyField(Author)
    year = models.IntegerField()
    loc = models.PointField(srid=4326, null=True, blank=True)
    country = models.CharField(max_length=64)
    city = models.CharField(max_length=64)
    event = models.TextField()
