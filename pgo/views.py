from __future__ import unicode_literals

import json

from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.text import slugify
from django.views.generic import (
    DetailView, ListView, TemplateView, RedirectView,
)

from pgo.models import (
    Pokemon, Move, Moveset, Type, WeatherCondition, DEFAULT_ORDER
)


class SortMixin(ListView):
    def get(self, request, *args, **kwargs):
        sort_by = slugify(request.GET.get('sort_by'))
        sort_key = slugify(request.GET.get('sort_key'))

        if sort_by and sort_by != 'none':
            if sort_key == sort_by:
                self.sort_by = ('-{}'.format(sort_by),)
            else:
                self.sort_by = (sort_by,)
        else:
            self.sort_by = self._get_default_order()
        return super(SortMixin, self).get(request, args, kwargs)

    def _get_default_order(self):
        return DEFAULT_ORDER[self.model.__name__]

    def get_queryset(self):
        if self.sort_by:
            try:
                return self.model.objects.order_by(*self.sort_by)
            except Exception:
                raise Http404
        return self.model.objects

    def get_context_data(self, **kwargs):
        context = super(SortMixin, self).get_context_data(**kwargs)
        context['sort_key'] = '&'.join(self.sort_by)
        return context


class PGoHomeView(TemplateView):
    template_name = 'pgo/pgo_home.html'


class PokemonListView(SortMixin):
    model = Pokemon
    paginate_by = 151

    def dispatch(self, request, *args, **kwargs):
        pokemon_id = int(request.GET.get('pokemon_id', 0))
        if pokemon_id != 0:
            pokemon_slug = get_object_or_404(Pokemon, pk=pokemon_id).slug
            return redirect(reverse('pgo:pokemon-detail', kwargs={'slug': pokemon_slug}))

        self.type_id = int(request.GET.get('type_id', 0))
        return super(PokemonListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(PokemonListView, self).get_queryset()
        if self.type_id != 0:
            qs = qs.filter(primary_type_id=self.type_id)

        return qs.select_related('primary_type', 'secondary_type')

    def get_context_data(self, **kwargs):
        context = super(PokemonListView, self).get_context_data(**kwargs)
        data = {
            'pokemon_data': self.model.objects.values_list('id', 'name'),
            'types': Type.objects.values_list('id', 'name'),
            'type_id': self.type_id,
        }
        context.update(data)
        return context


class PokemonDetailView(DetailView):
    model = Pokemon

    def get_queryset(self):
        return self.model.objects.select_related(
            'primary_type', 'secondary_type').prefetch_related(
            'quick_moves', 'cinematic_moves')

    def get_context_data(self, **kwargs):
        context = super(PokemonDetailView, self).get_context_data(**kwargs)

        context['movesets'] = Moveset.objects.filter(pokemon=self.object)
        return context


class MoveListView(SortMixin):
    model = Move

    def get(self, request, *args, **kwargs):
        self.move_id = int(request.GET.get('move_id', 0))

        return super(MoveListView, self).get(request, args, kwargs)

    def get_queryset(self):
        qs = super(MoveListView, self).get_queryset()

        if self.move_id != 0:
            qs = qs.filter(id=self.move_id)
        return qs.select_related('move_type')

    def get_context_data(self, **kwargs):
        context = super(MoveListView, self).get_context_data(**kwargs)
        data = {
            'move_data': self.model.objects.values_list('id', 'name'),
            'move_id': self.move_id,
        }
        context.update(data)
        return context


class MoveDetailView(DetailView):
    model = Move


class TypeListView(ListView):
    model = Type


class TypeDetailView(DetailView):
    model = Type


class MovesetListView(SortMixin):
    model = Moveset
    template_name = 'pgo/moveset_list.html'
    paginate_by = 200

    def get(self, request, *args, **kwargs):
        self.pokemon_id = int(request.GET.get('pokemon_id', 0))
        self.moveset_filter = request.GET.get('moveset-filter')

        return super(MovesetListView, self).get(request, args, kwargs)

    def get_queryset(self):
        qs = super(
            MovesetListView, self).get_queryset().select_related('pokemon')

        if self.pokemon_id != 0:
            qs = qs.filter(pokemon_id=self.pokemon_id)
        if self.moveset_filter:
            qs = qs.filter(key__icontains=self.moveset_filter)
        return qs

    def get_context_data(self, **kwargs):
        context = super(MovesetListView, self).get_context_data(**kwargs)
        data = {
            'pokemon_data': Pokemon.objects.values_list('id', 'name'),
            'pokemon_id': self.pokemon_id,
            'moveset_filter': self.moveset_filter,
        }
        context.update(data)
        return context


class MovesetDetailView(DetailView):
    model = DetailView


class BreakpointCalcRedirectView(RedirectView):
    permanent = True
    pattern_name = 'pgo:breakpoint-calc'


class CalculatorInitialDataMixin(TemplateView):
    def get(self, request, *args, **kwargs):
        try:
            self.initial_data = json.dumps(self._process_get_params(request.GET))
        except (TypeError, ValueError,
                Pokemon.DoesNotExist, Move.DoesNotExist, WeatherCondition.DoesNotExist):
            self.initial_data = {}
        return super(CalculatorInitialDataMixin, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CalculatorInitialDataMixin, self).get_context_data(**kwargs)

        data = {
            'pokemon_data': Pokemon.objects.values_list('id', 'name', 'pgo_attack', 'pgo_defense'),
            'attack_iv_range': list(xrange(15, -1, -1)),
            'weather_conditions': WeatherCondition.objects.values_list('id', 'name'),
            'initial_data': self.initial_data,
        }
        context.update(data)
        return context


class BreakpointCalculatorView(CalculatorInitialDataMixin):
    template_name = 'pgo/breakpoint_calc.html'

    def _process_get_params(self, params):
        return {}


class GoodToGoView(CalculatorInitialDataMixin):
    template_name = 'pgo/good_to_go.html'

    def _process_get_params(self, params):
        return {
            'attacker_id': Pokemon.objects.get(slug=slugify(params.get('attacker'))).pk,
            'attack_iv': int(params.get('attack_iv')),
            'quick_move_id': Move.objects.get(slug=slugify(params.get('quick_move'))).pk,
            'cinematic_move_id': Move.objects.get(slug=slugify(params.get('cinematic_move'))).pk,
            'weather_id': WeatherCondition.objects.get(slug=slugify(params.get('weather'))).pk,
            'current_raid_bosses': bool(int(params.get('current_raid_bosses'))),
            'old_raid_bosses': bool(int(params.get('old_raid_bosses'))),
            'relevant_defenders': bool(int(params.get('relevant_defenders'))),
        }
