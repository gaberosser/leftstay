# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-25 03:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='propertyurl',
            name='deactivated',
            field=models.DateTimeField(auto_created=True, help_text=b'Timestamp for deactivation', null=True),
        ),
        migrations.AlterField(
            model_name='propertyurl',
            name='last_accessed',
            field=models.DateTimeField(help_text=b'Timestamp for previous access', null=True),
        ),
        migrations.AlterField(
            model_name='propertyurl',
            name='last_known_status',
            field=models.IntegerField(blank=True, choices=[(1, b'active'), (2, b'removed'), (3, b'suspended'), (4, b'not found')], null=True),
        ),
        migrations.AlterField(
            model_name='propertyurl',
            name='last_status_code',
            field=models.IntegerField(help_text=b'Status code obtained on previous update', null=True),
        ),
        migrations.AlterField(
            model_name='propertyurl',
            name='last_updated',
            field=models.DateTimeField(help_text=b'Timestamp for previous update', null=True),
        ),
    ]
