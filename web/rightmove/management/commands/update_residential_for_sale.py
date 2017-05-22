from django.core.management.base import BaseCommand
from rightmove import getter
from leftstay.settings import DEFAULT_USER_AGENT


class Command(BaseCommand):
    help = 'Get sitemaps. Update URLs.'

    def handle(self, *args, **options):
        # set the location of any homes that are not geolocated
        getter.update_property_sitemaps(user_agent=DEFAULT_USER_AGENT)
        getter.update_property_urls()
