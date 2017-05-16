# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-12 08:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rightmove', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='propertyforsale',
            name='building_situation',
            field=models.IntegerField(blank=True, choices=[(1, b'Detached'), (2, b'Semi detached'), (3, b'End terrace'), (4, b'Mid terrace'), (5, b'Link detached'), (6, b'Flat'), (7, b'Ground floor')], null=True),
        ),
    ]
