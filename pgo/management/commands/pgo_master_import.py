# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
from decimal import Decimal
from math import sqrt, pow

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from pgo.models import (
    CPM,
    Pokemon,
    Move,
    Type,
    TypeAdvantage,
    TypeEffectivness,
)
TYPE_EFFECTIVNESS = {
    'Super effective': 1.25,
    'Not very effective': 0.8,
    'Neutral': 1.0,
}
TYPE_IMPORT_ORDER = (
    'normal',
    'fighting',
    'flying',
    'poison',
    'ground',
    'rock',
    'bug',
    'ghost',
    'steel',
    'fire',
    'water',
    'grass',
    'electric',
    'psychic',
    'ice',
    'dragon',
    'dark',
    'fairy',
)


class Command(BaseCommand):
    help = '''
        Build the CPM, Pokemon, Move and Type models, parsed from the .csv source file.
    '''

    def get_or_create_cpm(self, value, level):
        obj, created = CPM.objects.get_or_create(
            level=level,
            defaults={'value': value}
        )

    def get_or_create_type(self, slug):
        if slug != '':
            obj, created = Type.objects.get_or_create(
                slug=slug,
                defaults={'name': slug.capitalize()}
            )
            return obj

    def get_or_create_type_effectivness(self, name, scalar):
        obj, created = TypeEffectivness.objects.get_or_create(
            slug=slugify(name),
            defaults={'scalar': Decimal(scalar), 'name': name}
        )

    def get_or_create_type_advantage(self, first_type, second_type, effectivness):
        relation = '{0}:{1}'.format(first_type.slug, second_type.slug)
        obj, created = TypeAdvantage.objects.get_or_create(
            relation=relation,
            defaults={
                'first_type': first_type,
                'second_type': second_type,
                'effectivness': effectivness,
            }
        )

    def get_or_create_pokemon(self, number):
        obj, created = Pokemon.objects.get_or_create(number=number)
        return obj

    def get_or_create_move(self, slug, move_category):
        obj, created = Move.objects.get_or_create(
            slug=slug,
            defaults={
                'name': slug.replace('-', ' ').title(),
                'move_category': move_category
            }
        )
        return obj

    def _process_cpm(self, cpm):
        previous_value = None
        for cp_m in [(y, x + 1) for x, y in enumerate(cpm)]:
            value = cp_m[0]
            level = cp_m[1]
            self.get_or_create_cpm(value, level)

            if previous_value:
                halflevel_value = \
                    sqrt((pow(previous_value, 2) + pow(value, 2)) / 2.0)
                self.get_or_create_cpm(halflevel_value, level - 0.5)
                previous_value = None

            previous_value = value

    def _process_type_advantages(self, type_and_scalar_data):
        for first_type_slug, type_data_and_scalars in type_and_scalar_data.items():
            first_type = Type.objects.get(slug=first_type_slug)

            for data in type_data_and_scalars:
                for second_type_slug, scalar in data.items():
                    second_type = Type.objects.get(slug=second_type_slug)
                    self.get_or_create_type_advantage(first_type, second_type,
                        TypeEffectivness.objects.get(scalar=scalar))

    def _process_pokemon(self, pokemon_data):
        for pokemon_number, data in pokemon_data.items():
            pokemon = self.get_or_create_pokemon(pokemon_number)

            pokemon_types = []
            pokemon_moves = []
            for detail in data:
                if 'slug' in detail:
                    slug = detail['slug']
                    if slug == 'nidoran-female':
                        slug = unicode('nidoran♀')
                    if slug == 'nidoran-male':
                        slug = unicode('nidoran♂')

                    name = slug.capitalize()
                    if slug == 'mr-mime':
                        name = 'Mr. Mime'
                    if slug == 'ho-oh':
                        name = 'Ho-Oh'

                    pokemon.slug = slug
                    pokemon.name = name

                if 'pokemon_types' in detail:
                    for pokemon_type in detail['pokemon_types']:
                        pokemon_types.append(
                            self.get_or_create_type(slugify(pokemon_type)))

                    if len(pokemon_types) == 2:
                        pokemon.secondary_type = pokemon_types[1]
                    pokemon.primary_type = pokemon_types[0]

                if 'stats' in detail:
                    pokemon.pgo_stamina = detail['stats'][0]['stamina']
                    pokemon.pgo_attack = detail['stats'][1]['attack']
                    pokemon.pgo_defense = detail['stats'][2]['defense']

                if 'moves' in detail:
                    for move_name in detail['moves']['quick']:
                        pokemon.quick_moves.add(self.get_or_create_move(
                            slugify(move_name.replace('_', '-')), 'QK'
                        ))

                    for move_name in detail['moves']['cinematic']:
                        pokemon.cinematic_moves.add(self.get_or_create_move(
                            slugify(move_name.replace('_', '-')), 'CC'
                        ))
            pokemon.save()

    def _process_moves(self, move_data):
        for move_slug, data in move_data.items():
            move = None
            for detail in data:
                if 'move_category' in detail:
                    move = self.get_or_create_move(
                        move_slug, detail['move_category'])
                if 'move_type' in detail:
                    move.move_type_id = \
                        self.get_or_create_type(detail['move_type']).id
                if 'power' in detail:
                    move.power = detail['power']
                if 'duration' in detail:
                    move.duration = detail['duration']
                if 'damage_window_start' in detail:
                    move.damage_window_start = detail['damage_window_start']
                if 'damage_window_end' in detail:
                    move.damage_window_end = detail['damage_window_end']
                if 'energy_delta' in detail:
                    move.energy_delta = detail['energy_delta']
            move.save()

    def _next(self, csv_object, slice_start=None, slice_end=None):
        return csv_object.next()[0][slice_start:slice_end].strip()

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', type=str)

    def handle(self, *args, **options):
        path = '{0}{1}'.format(settings.BASE_DIR, '/pgo/resources/master.csv')
        file_path = options.get('path') if options.get('path') else path

        for name, scalar in TYPE_EFFECTIVNESS.items():
            self.get_or_create_type_effectivness(name, scalar)

        cpm_data = []
        type_data = {}
        pokemon_data = {}
        move_data = {}

        with open(file_path, 'rb') as csvfile:
            csv_object = csv.reader(csvfile, delimiter=b'\n', quotechar=b'|')

            for row in csv_object:
                if 'cp_multiplier' in row[0]:
                    cpm_data.append(Decimal(row[0].strip()[15:]))

                if 'template_id: "POKEMON_TYPE' in row[0]:
                    key = slugify(row[0][29:].replace('"', ''))
                    type_data[key] = ''
                    self._next(csv_object)

                    type_data_scalars = []
                    for n in range(1, 19):
                        type_data_scalars.append(
                            {TYPE_IMPORT_ORDER[n - 1]: self._next(csv_object, 19)})
                    type_data[key] = type_data_scalars

                if 'template_id: "V' in row[0]:
                    template_id = '#{0}'.format(row[0][18:21])

                    if 'pokemon_settings' in self._next(csv_object):
                        # name
                        data = []
                        data.append({'slug': slugify(
                            self._next(csv_object, 15).replace('_', '-')
                        )})
                        self._next(csv_object)
                        # types
                        data.append({
                            'pokemon_types': (
                                self._next(csv_object, 23),
                                self._next(csv_object, 25)
                            )
                        })

                        while 'stats' not in self._next(csv_object):
                            pass
                        # stats
                        data.append({
                            'stats': (
                                {'stamina': self._next(csv_object, 20)},
                                {'attack': self._next(csv_object, 19)},
                                {'defense': self._next(csv_object, 20)}
                            )
                        })
                        self._next(csv_object)

                        # moves
                        quick = []
                        cinematic = []
                        next_line = self._next(csv_object)

                        while 'moves' in next_line:
                            if 'quick_moves' in next_line:
                                quick.append(next_line[13:-5])
                            if 'cinematic_moves' in next_line:
                                cinematic.append(next_line[17:])
                            next_line = self._next(csv_object)

                        moves = {
                            'quick': quick,
                            'cinematic': cinematic
                        }
                        data.append({'moves': moves})
                        pokemon_data[template_id] = data
                    else:
                        data = []
                        move_slug = slugify(
                            self._next(csv_object, 17).replace('_', '-'))
                        move_category = 'CC'
                        if 'blastoise' in move_slug:
                            continue

                        if 'fast' in move_slug:
                            move_category = 'QK'
                            move_slug = move_slug[:-5]
                        self._next(csv_object)

                        # name & category
                        data.append({'move_category': move_category})
                        # move type
                        data.append(
                            {'move_type': slugify(self._next(csv_object, 31))})
                        # power

                        if move_slug not in ['transform', 'splash']:
                            data.append({'power': self._next(csv_object, 11)})

                        while 'vfx_name' not in self._next(csv_object):
                            pass

                        # durations & delta
                        data.append({
                            'duration': self._next(csv_object, 16)})
                        data.append({
                            'damage_window_start': self._next(csv_object, 27)})
                        data.append({
                            'damage_window_end': self._next(csv_object, 25)})

                        if move_slug not in ['transform', 'struggle']:
                            data.append({
                                'energy_delta': self._next(csv_object, 17)})
                        move_data[move_slug] = data

        self._process_pokemon(pokemon_data)
        self._process_type_advantages(type_data)
        self._process_cpm(cpm_data)
        self._process_moves(move_data)
