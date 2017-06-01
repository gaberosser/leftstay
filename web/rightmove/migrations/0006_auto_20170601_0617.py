# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-01 06:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rightmove', '0005_auto_20170530_0436'),
    ]

    operations = [
        migrations.AlterField(
            model_name='propertyforsale',
            name='building_type',
            field=models.IntegerField(choices=[(1, b'Flat/apartment'), (2, b'Bungalow'), (3, b'Studio flat'), (4, b'Retirement property'), (5, b'Maisonette'), (6, b'Town house'), (7, b'House'), (8, b'Country house'), (9, b'Penthouse'), (10, b'Villa'), (11, b'Lodge'), (12, b'Chalet'), (13, b'Barn conversion'), (14, b'Cottage'), (15, b'Duplex'), (16, b'Mobile home'), (17, b'Park home')]),
        ),
    ]
