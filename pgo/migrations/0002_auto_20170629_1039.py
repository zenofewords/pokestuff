# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-29 10:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pgo', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='moveset',
            options={'ordering': ('pokemon__name', '-weave_damage')},
        ),
        migrations.AlterField(
            model_name='typeeffectivnessscalar',
            name='scalar',
            field=models.DecimalField(decimal_places=3, max_digits=4),
        ),
    ]
