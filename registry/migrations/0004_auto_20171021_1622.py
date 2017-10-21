# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-10-21 16:22
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registry', '0003_auto_20171015_2052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trainer',
            name='level',
            field=models.PositiveIntegerField(blank=True, default=0, help_text='Defaults to 0 if not set.', null=True, validators=[django.core.validators.MaxValueValidator(40)]),
        ),
    ]