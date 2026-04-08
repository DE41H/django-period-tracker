from django.db.models import QuerySet

from cycle.models import Phase


def get_by_name(name: str) -> Phase | None:
    return Phase.objects.filter(name__iexact=name).first()


def get_for_cycle_day(cycle_day: int) -> Phase | None:
    return Phase.objects.filter(
        typical_start_day__lte=cycle_day,
        typical_end_day__gte=cycle_day,
    ).first()


def all() -> QuerySet[Phase]:
    return Phase.objects.all()
