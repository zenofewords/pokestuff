from __future__ import unicode_literals

import json
from decimal import Decimal, InvalidOperation, getcontext
from math import pow, sqrt, floor

from django.apps import apps
from django.utils.text import slugify
from django.views.generic import (
    DetailView,
    RedirectView,
    TemplateView,
)

from pgo.mixins import ListViewOrderingMixin
from pgo.models import (
    CPM,
    Friendship,
    Move,
    Moveset,
    Pokemon,
    PokemonMove,
    RaidTier,
    WeatherCondition,
)

from zenofewords.models import SiteNotification


class BreakpointCalcRedirectView(RedirectView):
    permanent = True
    pattern_name = 'pgo:breakpoint-calc'


class CalculatorInitialDataMixin(TemplateView):
    def get(self, request, *args, **kwargs):
        try:
            self.initial_data = json.dumps(self._process_get_params(request.GET))
        except (TypeError, ValueError, LookupError, InvalidOperation,
                Pokemon.DoesNotExist, Move.DoesNotExist, WeatherCondition.DoesNotExist):
            self.initial_data = {}
        return super(CalculatorInitialDataMixin, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CalculatorInitialDataMixin, self).get_context_data(**kwargs)
        defender_cpm_data = (
            list(RaidTier.objects.order_by('order').values_list('tier', 'raid_cpm__value')) +
            list(CPM.objects.filter(level=40, raid_cpm=False).values_list('level', 'value'))
        )

        data = {
            'attack_iv_range': list(range(15, -1, -1)),
            'weather_condition_data': WeatherCondition.objects.values_list('id', 'name'),
            'friendship': Friendship.objects.all(),
            'defender_cpm_data': defender_cpm_data,
            'initial_data': self.initial_data,
            'site_notifications': SiteNotification.objects.all(),
        }
        context.update(data)
        return context

    def _get_object_id(self, model_name, value):
        try:
            return int(value)
        except ValueError:
            model = apps.get_model('pgo', model_name)
            return model.objects.get(slug=slugify(value)).pk


class BreakpointCalculatorView(CalculatorInitialDataMixin):
    template_name = 'pgo/breakpoint_calc.html'

    def _process_get_params(self, params):
        getcontext().prec = 11

        return {
            'attacker': self._get_object_id('Pokemon', params.get('attacker')),
            'attacker_level': float(params.get('attacker_level')),
            'attacker_quick_move': self._get_object_id(
                'Move', params.get('attacker_quick_move')),
            'attacker_cinematic_move': self._get_object_id(
                'Move', params.get('attacker_cinematic_move')),
            'attacker_atk_iv': int(params.get('attacker_atk_iv')),
            'weather_condition': self._get_object_id(
                'WeatherCondition', params.get('weather_condition')),
            'friendship_boost': str(params.get('friendship_boost')),
            'defender': self._get_object_id('Pokemon', params.get('defender')),
            'defender_quick_move': self._get_object_id(
                'Move', params.get('defender_quick_move')),
            'defender_cinematic_move': self._get_object_id(
                'Move', params.get('defender_cinematic_move')),
            'defender_cpm': str(Decimal(params.get('defender_cpm'))),
            'tab': slugify(params.get('tab', 'breakpoints')),
        }


class GoodToGoView(CalculatorInitialDataMixin):
    template_name = 'pgo/good_to_go.html'

    def _process_get_params(self, params):
        return {
            'attacker': self._get_object_id('Pokemon', params.get('attacker')),
            'attack_iv': int(params.get('attack_iv')),
            'quick_move': self._get_object_id('Move', params.get('quick_move')),
            'cinematic_move': self._get_object_id('Move', params.get('cinematic_move')),
            'weather_condition': self._get_object_id(
                'WeatherCondition', params.get('weather_condition')),
            'friendship_boost': str(params.get('friendship_boost')),
            'tier_3_6_raid_bosses': bool(params.get('tier_3_6_raid_bosses') == 'true'),
            'tier_1_2_raid_bosses': bool(params.get('tier_1_2_raid_bosses') == 'true'),
            'relevant_defenders': bool(params.get('relevant_defenders') == 'true'),
        }


class PvPView(TemplateView):
    template_name = 'pgo/pvp.html'


class PokemonListView(ListViewOrderingMixin):
    template_name = 'pgo/pokemon_list.html'
    queryset = Pokemon.objects.select_related('primary_type', 'secondary_type')
    default_ordering = ('number', 'name',)
    ordering_fields = (
        'number', 'slug', 'primary_type', 'secondary_type',
        'pgo_attack', 'pgo_defense', 'pgo_stamina', 'maximum_cp'
    )
    values_list_args = ('slug', 'name',)


class MoveListView(ListViewOrderingMixin):
    template_name = 'pgo/move_list.html'
    queryset = Move.objects.select_related('move_type')
    default_ordering = ('-category', 'name',)
    ordering_fields = (
        'slug', 'category', 'move_type', 'power', 'energy_delta', 'duration',
        'damage_window_start', 'damage_window_end', 'dps', 'eps',
        'pvp_power', 'pvp_energy_delta', 'pvp_duration', 'dpt', 'ept', 'dpe',
    )
    values_list_args = ('slug', 'name',)


class PokemonDetailView(DetailView):
    model = Pokemon

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cpm_qs = CPM.objects.filter(
            raid_cpm=False,
            level__in=[1, 15, 20, 25, 30, 35, 40]
        )
        moveset_qs = Moveset.objects.filter(
            pokemon_id=self.object.pk
        )
        context.update({
            'data': Pokemon.objects.values_list('slug', 'name'),
            'pokemon_stats': [(
                int(x.level),
                floor(x.value * (self.object.pgo_attack + 15)),
                floor(x.value * (self.object.pgo_defense + 15)),
                floor(x.value * (self.object.pgo_stamina + 15)),
                self._calculate_cp(float(x.value)),
            ) for x in cpm_qs.order_by('-level')],
            'movesets': Moveset.objects.filter(
                pokemon_id=self.object.pk
            ).order_by('-weave_damage__4'),
            'pokemon_moves': PokemonMove.objects.filter(
                pokemon_id=self.object.pk
            ).select_related(
                'move__move_type',
            ).order_by(
                '-move__category', '-score',
            ),
        })
        return context

    def _calculate_cp(self, value):
        return floor(
            (self.object.pgo_attack + 15)
            * sqrt(self.object.pgo_defense + 15)
            * sqrt(self.object.pgo_stamina + 15)
            * pow(value, 2) / 10.0
        )

class MoveDetailView(DetailView):
    model = Move

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        move_type = self.object.move_type
        effectivness = move_type.strong + move_type.feeble + move_type.puny
        context.update({
            'data': Move.objects.values_list('slug', 'name'),
            'effectivness': effectivness,
            'pokemon_moves': PokemonMove.objects.filter(
                move_id=self.object.pk
            ).select_related(
                'pokemon__primary_type',
                'pokemon__secondary_type',
            ).order_by(
                '-pokemon__maximum_cp',
            ),
        })
        return context
