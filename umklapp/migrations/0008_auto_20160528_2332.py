# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-28 23:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('umklapp', '0007_story_title'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='storypart',
            options={'ordering': ['position']},
        ),
    ]
