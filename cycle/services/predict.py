from datetime import date, timedelta

from django.db.transaction import atomic

from cycle.models import Day, FlowLevel, Phase, User
from cycle.services.day import get_period_dates


MEASUREMENT_NOISE = 2.0
PREDICTION_NOISE = MEASUREMENT_NOISE * 2
PROCESS_NOISE = 0.5
CYCLES_TO_PREDICT = 3
DEFAULT_PERIOD_LENGTH = 5


@atomic
def update_kalman_estimate(user_id: int, observed_cycle_length: float) -> None:
    user = User.objects.select_for_update().get(pk=user_id)
    K = user.kalman_error / (user.kalman_error + MEASUREMENT_NOISE)
    user.kalman_estimate = (
        user.kalman_estimate + K * (observed_cycle_length - user.kalman_estimate)
    )
    user.kalman_error = (1 - K) * user.kalman_error
    user.save(update_fields=['kalman_estimate', 'kalman_error'])


def _average_period_length(real_lengths: list[int], predicted_lengths: list[int]) -> int:  # noqa: E501
    all_lengths = real_lengths + predicted_lengths
    if all_lengths:
        return max(1, round(sum(all_lengths) / len(all_lengths)))
    return DEFAULT_PERIOD_LENGTH


def _flow_for_period_offset(offset: int, period_length: int) -> str:
    if period_length <= 2:
        return FlowLevel.MEDIUM
    if offset == 0 or offset == period_length - 1:
        return FlowLevel.LIGHT
    mid = (period_length - 1) / 2
    if abs(offset - mid) <= 0.5:
        return FlowLevel.HEAVY
    return FlowLevel.MEDIUM


def _phase_for_scaled_day(phases: list[Phase], scaled_day: int) -> Phase | None:
    for phase in phases:
        if phase.typical_start_day <= scaled_day <= phase.typical_end_day:
            return phase
    return None


@atomic
def generate_predictions(user_id: int, from_date: date) -> None:
    user = User.objects.select_for_update().get(pk=user_id)
    phases = list(
        Phase.objects
        .prefetch_related('symptoms')
        .order_by('typical_start_day')
    )
    phase_symptoms: dict[int, list] = {p.pk: list(p.symptoms.all()) for p in phases}  # pyright: ignore[reportAttributeAccessIssue]
    real_period_lengths = [
        (end - start).days + 1
        for start, end in get_period_dates(user_id)
        if start < from_date
    ]
    kalman_estimate = user.kalman_estimate
    kalman_error = user.kalman_error
    predicted_period_lengths: list[int] = []
    to_create: list[Day] = []
    period_start = from_date
    for _ in range(CYCLES_TO_PREDICT):
        cycle_length = max(21, round(kalman_estimate))
        period_length = (
            _average_period_length(real_period_lengths, predicted_period_lengths)
        )
        ovulation_day = cycle_length - 14
        fertile_start = max(1, ovulation_day - 5)
        fertile_end = min(cycle_length, ovulation_day + 1)
        for day_num in range(1, cycle_length + 1):
            scaled = max(1, round((day_num / cycle_length) * 28))
            is_period = day_num <= period_length
            is_fertile = fertile_start <= day_num <= fertile_end
            to_create.append(
                Day(
                    user=user,
                    date=period_start + timedelta(days=day_num - 1),
                    flow_level=(
                        _flow_for_period_offset(day_num - 1, period_length)
                        if is_period else FlowLevel.NONE
                    ),
                    fertile=is_fertile,
                    phase=_phase_for_scaled_day(phases, scaled),
                    prediction=True,
                )
            )
        kalman_error += PROCESS_NOISE
        K = kalman_error / (kalman_error + PREDICTION_NOISE)
        kalman_estimate = kalman_estimate + K * (cycle_length - kalman_estimate)
        kalman_error = (1 - K) * kalman_error
        predicted_period_lengths.append(period_length)
        period_start += timedelta(days=cycle_length)
    Day.objects.filter(user=user, prediction=True).delete()
    Day.objects.bulk_create(to_create, ignore_conflicts=True)
    predicted_days = (
        Day.objects.filter(user=user, prediction=True).only('pk', 'phase_id')
    )
    Through = Day.symptoms.through
    Through.objects.bulk_create(
        [
            Through(day_id=day.pk, symptom_id=s.pk)
            for day in predicted_days
            for s in phase_symptoms.get(day.phase_id, [])  # pyright: ignore[reportAttributeAccessIssue]
        ]
    )
