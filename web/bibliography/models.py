from django.contrib.gis.db import models
import re


def shorten_journal(journal):
    short_words = ['of', 'and', 'the', 'for']
    replacements = [
        ('journal', 'J.'),
        ('international', 'Intl.'),
        ('mathematical', 'Math.'),
        ('bulletin', 'Bull.'),
        ('society', 'Soc.'),
        ('transactions', 'Trans.'),
        ('computational', 'Comp.'),
        ('proceedings', 'Proc.'),
        (r'biolog[^ ]*', 'Biol.'),
        ('quantitative', 'Quant.'),
        ('crimin[^ ]*', 'Criminol.'),
        ('geographical', 'Geog.'),
        ('science[^ ]*', 'Sci.'),
        ('inform[^ ]*', 'Inf.'),
        ('applied', 'Appl.')
    ]
    # sw_regex = re.compile(r' +| +'.join(short_words), flags=re.I)
    sw_regex = re.compile(r'\b(%s)\W' % '|'.join(short_words), flags=re.I)
    journal = re.sub(sw_regex, ' ', journal)
    for match, repl in replacements:
        journal = re.sub(match, repl, journal, flags=re.I)
    return journal


class Author(models.Model):
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    middle_initials = models.CharField(max_length=4, help_text="Any initials, without space/comma", null=True, blank=True)
    make_bold = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s %s" % (self.first_name, self.last_name)


class Publication(models.Model):
    title = models.TextField()
    authors = models.ManyToManyField(Author, through='PublicationAuthorship', related_name='authors')
    year = models.IntegerField()
    journal = models.TextField()
    volume = models.CharField(max_length=8, null=True, blank=True)
    edition = models.CharField(max_length=8, null=True, blank=True)
    page_start = models.CharField(max_length=8, null=True, blank=True)
    page_end = models.CharField(max_length=8, null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return "%s (%d)" % (shorten_journal(self.journal), self.year)


class Presentation(models.Model):
    title = models.TextField()
    authors = models.ManyToManyField(Author)
    year = models.IntegerField()
    loc = models.PointField(srid=4326, null=True, blank=True)
    country = models.CharField(max_length=64)
    city = models.CharField(max_length=64)
    event = models.TextField()


class PublicationAuthorship(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    order = models.IntegerField()
    joint = models.BooleanField(default=False)

    def save(self, **kwargs):
        qset = self.__class__.objects.filter(
            publication=self.publication,
            author=self.author,
            order=self.order,
            joint=False
        )
        if qset.exists():
            raise models.exceptions.ValidationError("An authorship already exists and joint is False.")
        super(PublicationAuthorship, self).save(**kwargs)