from django.db import models
from django.db.models import Q
from django.views import generic

from cycle.models import Phase, Symptom, Day

# Create your views here.

class SymptomListView(generic.ListView):
    model = Symptom
    template_name = 'symptom_list.html'
    context_object_name = 'symptoms'
    paginate_by = 20

    def get_queryset(self) -> models.query.QuerySet[_M]:  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        qs = super().get_queryset()
        query = self.request.GET.get('q', None)
        if query is not None:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(medical_term__icontains=query)
            )
        return qs


class SymptomDetailView(generic.DetailView):
    model = Symptom
    template_name = 'symptom_detail.html'
    context_object_name = 'symptom'

    def get_queryset(self) -> models.query.QuerySet[_M]:  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        return (
            super().get_queryset()
            .select_related('phase')
            .prefetch_related('related')
            .order_by('name')
        )


class PhaseListView(generic.ListView):
    model = Phase
    template_name = 'phase_list.html'
    context_object_name = 'phases'


class PhaseDetailView(generic.DetailView):
    model = Phase
    template_name = 'phase_detail.html'
    context_object_name = 'phase'


class DayDetailView(generic.DetailView):
    model = Day
    template_name = 'day_detail.html'
    context_object_name = 'day'

    def get_queryset(self) -> models.query.QuerySet[_M]:  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        return (
            super().get_queryset().
            select_related('phase').
            prefetch_related('symptoms')
        )

class DayUpdateView(generic.UpdateView):
    model = Day
