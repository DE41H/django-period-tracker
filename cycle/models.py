from django.conf import settings
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import Q, F
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField()
    uses_hormonal_contraception = models.BooleanField(default=False)
    is_trying_to_conceive = models.BooleanField(default=False)
    kalman_estimate = models.FloatField(default=28.0)
    kalman_error = models.FloatField(default=10.0)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class FlowLevel(models.TextChoices):
    LIGHT = 'light', 'Light'
    MEDIUM = 'medium', 'Medium'
    HEAVY = 'heavy', 'Heavy'
    NONE = 'none', 'None'


class SeverityLevel(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    POSITIVE = 'positive', 'Positive'
    NEUTRAL = 'neutral', 'Neutral'


class Phase(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )
    description = models.TextField()
    typical_start_day = models.PositiveSmallIntegerField()
    typical_end_day = models.PositiveSmallIntegerField()
    dominant_hormones = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(typical_end_day__gte=F('typical_start_day')),
                name='typical_end_day_after_typical_start_day'
            )
        ]

    def __str__(self) -> str:
        return f'[ Phase: {self.pk} ]'


class Day(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    flow_level = models.CharField(
        max_length=10,
        choices=FlowLevel.choices,
        default=FlowLevel.NONE
    )
    symptoms = models.ManyToManyField('cycle.Symptom', blank=True)
    spotting = models.BooleanField(default=False)
    notes = models.TextField(
        validators=(MaxLengthValidator(2000),),
        blank=True,
        default=''
    )
    phase = models.ForeignKey(
        'cycle.Phase',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    fertile = models.BooleanField(default=False, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'date'], name='unique_user_date')
        ]

    def __str__(self) -> str:
        return f'[ Day: {self.pk} ]'


class Symptom(models.Model):
    name = models.CharField(max_length=100 ,unique=True)
    medical_term = models.CharField(max_length=200)
    phase = models.ForeignKey(
        'cycle.Phase',
        on_delete=models.CASCADE,
        related_name='symptoms'
    )
    severity = models.CharField(
        max_length=10,
        choices=SeverityLevel.choices
    )
    probability = models.FloatField(
        validators=(MinValueValidator(0.0), MaxValueValidator(1.0))
    )
    description = models.TextField()
    typical_start_day = models.PositiveSmallIntegerField()
    typical_end_day = models.PositiveSmallIntegerField()
    related = models.ManyToManyField('self', blank=True)
    tips = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [
            CheckConstraint(
                condition=Q(typical_end_day__gte=F('typical_start_day')),
                name='symptom_typical_end_day_after_start_day'
            )
        ]

    def __str__(self) -> str:
        return f'[ Symptom: {self.pk} ]'
