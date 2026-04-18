from django.dispatch import receiver
from django.db.models.signals import post_save
from cycle.models import Day

@receiver(post_save, sender=Day)
def on_day_saved(sender, instance, created, update_fields, raw, **kwargs):
    pass
