import datetime

from django.db.models import QuerySet

from cycle.models import Day, FlowLevel, Symptom


def create(
    user_id: int,
    date: datetime.date,
    flow_level: FlowLevel = FlowLevel.NONE,
) -> Day:
    return Day.objects.create(user_id=user_id, date=date, flow_level=flow_level)


def get(user_id: int, date: datetime.date) -> Day | None:
    return Day.objects.filter(user_id=user_id, date=date).first()


def get_range(
    user_id: int,
    start_date: datetime.date,
    end_date: datetime.date,
) -> QuerySet[Day]:
    return Day.objects.filter(
        user_id=user_id,
        date__gte=start_date,
        date__lte=end_date,
    ).order_by('date')


def update(day: Day, **fields) -> Day:
    for attr, value in fields.items():
        setattr(day, attr, value)
    day.save(update_fields=list(fields.keys()))
    return day


def delete(day: Day) -> None:
    day.delete()


def add_symptom(day: Day, symptom: Symptom) -> None:
    day.symptoms.add(symptom)


def remove_symptom(day: Day, symptom: Symptom) -> None:
    day.symptoms.remove(symptom)
