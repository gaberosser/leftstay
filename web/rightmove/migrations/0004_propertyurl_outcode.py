# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-30 04:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rightmove', '0003_auto_20170526_0522'),
    ]

    operations = [
        migrations.AddField(
            model_name='propertyurl',
            name='outcode',
            field=models.IntegerField(blank=True, help_text=b'Rightmove integer outcode', null=True),
        ),
    ]
