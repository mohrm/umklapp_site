# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-20 11:57


from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('umklapp', '0018_story_read_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='last_action',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
