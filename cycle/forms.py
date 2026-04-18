from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import CheckboxSelectMultiple

from cycle.models import Day, User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'email',
            'date_of_birth',
            'uses_hormonal_contraception',
            'is_trying_to_conceive'
        )


class DayLogForm(forms.ModelForm):
    class Meta:
        model = Day
        fields = ('date', 'flow_level', 'symptoms', 'spotting', 'notes')
        widgets = {
            'symptoms': CheckboxSelectMultiple(),
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
