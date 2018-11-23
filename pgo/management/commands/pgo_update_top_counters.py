# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-06-09 12:34
from __future__ import unicode_literals

from math import pow
from django.core.management.base import BaseCommand

from pgo.models import (
    CPM,
    TopCounter,
)
from pgo.utils import MAX_IV


class Command(BaseCommand):
    help = 'Update TopCounter hp, multiplier, and score.'

    def _update_top_counter(self, top_counter, max_cpm_value):
        top_counter.score = int(
            pow(top_counter.highest_dps, 5) / 100000 *
            (top_counter.counter.pgo_defense * top_counter.counter.pgo_stamina) / 100
        )
        top_counter.multiplier = (top_counter.defender.pgo_attack + MAX_IV) / (top_counter.counter.pgo_defense + MAX_IV)
        top_counter.counter_hp = (top_counter.counter.pgo_stamina + MAX_IV) * max_cpm_value
        top_counter.save()

    def add_arguments(self, parser):
        parser.add_argument(
            '--attacker',
            action='append',
            dest='attackers',
            default=[],
            help='Expects a list of attacker slugs (--attacker="slug" --attacker="slug2"',
        )
        parser.add_argument(
            '--defender',
            action='append',
            dest='defenders',
            default=[],
            help='Expects a list of defender slugs',
        )

    def handle(self, *args, **options):
        max_cpm_value = CPM.objects.get(level=40, raid_cpm=False).value
        top_counters_qs = TopCounter.objects.select_related('counter', 'defender')
        attackers = options['attackers']
        defenders = options['defenders']

        if attackers:
            top_counters_qs = top_counters_qs.filter(counter__slug__in=attackers)
        if defenders:
            top_counters_qs = top_counters_qs.filter(defender__slug__in=defenders)

        for top_counter in top_counters_qs:
            self._update_top_counter(top_counter, max_cpm_value)
