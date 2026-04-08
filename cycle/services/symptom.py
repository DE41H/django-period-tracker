from django.db.models import QuerySet
from cycle.models import Phase, Symptom


def get_by_name(name: str) -> Symptom | None:
    return Symptom.objects.filter(name__iexact=name).first()


def get_for_phase(phase: Phase) -> QuerySet[Symptom]:
    return Symptom.objects.filter(phase=phase)


def get_for_cycle_day(cycle_day: int) -> QuerySet[Symptom]:
    return Symptom.objects.filter(
        typical_start_day__lte=cycle_day,
        typical_end_day__gte=cycle_day,
    )


def get_related(symptom: Symptom) -> QuerySet[Symptom]:
    return symptom.related.all()
