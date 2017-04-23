from django.contrib.gis.db import models


class PropertyForSaleSitemap(models.Model):
    url = models.URLField(null=False, blank=False, unique=True)
    accessed = models.DateTimeField(help_text="Timestamp for access", auto_created=True)
    status_code = models.IntegerField()
    last_modified = models.DateField(help_text="Last modified date according to the sitemap XML")
    content = models.TextField()
