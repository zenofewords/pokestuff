# Generated by Django 2.2.5 on 2019-09-25 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pgo', '0031_remove_raidboss_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pokemonmove',
            name='score',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=4),
        ),
    ]
