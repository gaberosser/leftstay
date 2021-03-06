# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-14 05:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rightmove', '0008_delete_propertysitemap'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='propertybase',
            name='agent_address',
        ),
        migrations.RemoveField(
            model_name='propertybase',
            name='agent_tel',
        ),
        migrations.RemoveField(
            model_name='propertyurl',
            name='consecutive_failed_attempts',
        ),
        migrations.RemoveField(
            model_name='propertyurl',
            name='last_accessed',
        ),
        migrations.RemoveField(
            model_name='propertyurl',
            name='last_known_status',
        ),
        migrations.RemoveField(
            model_name='propertyurl',
            name='last_status_code',
        ),
        migrations.AddField(
            model_name='propertybase',
            name='agent_attribute',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='propertybase',
            name='url',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='property_set', to='rightmove.PropertyUrl'),
        ),
        migrations.AlterField(
            model_name='propertyforsale',
            name='building_type',
            field=models.IntegerField(choices=[(0, b'Unknown type'), (1, b'Flat/apartment'), (2, b'Bungalow'), (3, b'Studio flat'), (4, b'Retirement property'), (5, b'Maisonette'), (6, b'Town house'), (7, b'House'), (8, b'Country house'), (9, b'Penthouse'), (10, b'Villa'), (11, b'Lodge'), (12, b'Chalet'), (13, b'Barn conversion'), (14, b'Cottage'), (15, b'Duplex'), (16, b'Mobile home'), (17, b'Park home')]),
        ),
    ]
