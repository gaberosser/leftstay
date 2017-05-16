from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule


class Command(BaseCommand):
    help = "Create periodic tasks using celery beat (if not already created)"

    def handle(self, *args, **options):

        sch, cr = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='3',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        try:
            per = PeriodicTask.objects.get(name='RM sitemaps')
        except Exception:
            PeriodicTask.objects.create(
                crontab=sch,
                name='RM sitemaps',
                task='rightmove.tasks.update_property_urls',
            )

        sch, cr = CrontabSchedule.objects.get_or_create(
            minute='30',
            hour='3',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        try:
            per = PeriodicTask.objects.get(name='RM property for sale')
        except Exception:
            PeriodicTask.objects.create(
                crontab=sch,
                name='RM property for sale',
                task='rightmove.tasks.update_all_residential_for_sale',
            )
