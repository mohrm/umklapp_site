# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-28 19:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('umklapp', '0004_auto_20160528_1914'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storypart',
            name='owning_story',
        ),
    ]
