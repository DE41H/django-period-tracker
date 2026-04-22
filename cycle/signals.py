from django.dispatch import receiver
from django.db.models.signals import post_save
from cycle.services.day import is_period_start, get_last_period_start
from cycle.services.predict import update_kalman_estimate, generate_predictions

from cycle.models import Day, FlowLevel


@receiver(post_save, sender=Day)
def on_day_saved(sender, instance: Day, created, update_fields, raw, **kwargs):
    if raw or instance.prediction:
        return
    if instance.flow_level == FlowLevel.NONE:
        return
    if not is_period_start(instance.pk):
        return
    prev_start = get_last_period_start(instance.user.pk, before_date=instance.date)
    if prev_start is not None:
        cycle_length = (instance.date - prev_start.date).days
        if 21 <= cycle_length <= 45:
            instance.user.refresh_from_db(fields=['kalman_estimate', 'kalman_error'])
            update_kalman_estimate(instance.user.pk, float(cycle_length))
    instance.user.refresh_from_db(fields=['kalman_estimate', 'kalman_error'])
    generate_predictions(instance.user.pk, from_date=instance.date)
