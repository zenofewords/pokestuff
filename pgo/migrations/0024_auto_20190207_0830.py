# Generated by Django 2.1.5 on 2019-02-07 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pgo', '0023_auto_20190207_0829'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pokemonmove',
            name='score',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
    ]