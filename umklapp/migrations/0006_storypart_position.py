# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-28 19:51


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('umklapp', '0005_remove_storypart_owning_story'),
    ]

    operations = [
        migrations.AddField(
            model_name='storypart',
            name='position',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
