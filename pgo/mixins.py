from django.views.generic.list import ListView
from django.utils.text import slugify

from pgo.models import Type


class ListViewOrderingMixin(ListView):
    paginate_by = 100

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', None)

        if ordering and ordering.replace('-', '') in self.ordering_fields:
            return ordering
        return None

    def get_queryset(self):
        queryset = super().get_queryset()
        self.unfiltered_data = queryset
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'types': Type.objects.all(),
            'ordering': self.get_ordering(),
            'data': self.object_list.values_list(*self.values_list_args),
            'unfiltered_data': self.unfiltered_data.values_list(*self.values_list_args),
        })
        return context


class PresetMixin(object):
    def get(self, request, *args, **kwargs):
        self.preset = slugify(self.request.GET.get('preset', 'pvp'))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'preset': self.preset,
        })
        return context
