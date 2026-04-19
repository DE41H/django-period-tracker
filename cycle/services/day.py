from datetime import date, timedelta

from django.db.models import Exists, OuterRef

from cycle.models import Day, FlowLevel


def is_period_start(day_id: int) -> bool:
    day = Day.objects.get(pk=day_id)
    if day.flow_level == FlowLevel.NONE:
        return False
    prev_date = day.date - timedelta(days=1)
    return not Day.objects.filter(
        user=day.user,
        date=prev_date,
        prediction=False,
    ).exclude(flow_level=FlowLevel.NONE).exists()


def get_last_period_start(user_id: int, before_date: date) -> Day | None:
    prev_actual_with_flow = (
        Day.objects
        .filter(
            user=OuterRef('user'),
            date=OuterRef('date') - timedelta(days=1),
            prediction=False,
        ).exclude(flow_level=FlowLevel.NONE)
    )
    return (
        Day.objects
        .filter(user_id=user_id, date__lt=before_date, prediction=False)
        .exclude(flow_level=FlowLevel.NONE)
        .annotate(had_flow_yest=Exists(prev_actual_with_flow))
        .filter(had_flow_yest=False)
        .order_by('-date')
        .first()
    )


def get_period_dates(user_id: int) -> tuple[tuple[date, date], ...]:
    prev_actual_with_flow = (
        Day.objects
        .filter(
            user=OuterRef('user'),
            date=OuterRef('date') - timedelta(days=1),
            prediction=False,
        ).exclude(flow_level=FlowLevel.NONE)
    )
    next_actual_with_flow = Day.objects.filter(
        user=OuterRef('user'),
        date=OuterRef('date') + timedelta(days=1),
        prediction=False,
    ).exclude(flow_level=FlowLevel.NONE)

    base_qs = (
        Day.objects
        .filter(user_id=user_id, prediction=False)
        .exclude(flow_level=FlowLevel.NONE)
    )
    start_dates = list(
        base_qs
        .annotate(had_flow_yest=Exists(prev_actual_with_flow))
        .filter(had_flow_yest=False)
        .order_by('-date')
        .values_list('date', flat=True)
    )
    end_dates = list(
        base_qs
        .annotate(has_flow_tom=Exists(next_actual_with_flow))
        .filter(has_flow_tom=False)
        .order_by('-date')
        .values_list('date', flat=True)
    )
    return tuple(zip(start_dates, end_dates))
