# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-01 15:18


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('umklapp', '0009_teller_hasleft'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='is_public',
            field=models.BooleanField(default=False),
        ),
    ]
