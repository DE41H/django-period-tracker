from django.db import models
from django.db.models import Q
from django.views import generic
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from cycle.models import Phase, Symptom, Day, User

# Create your views here.


class DashboardRedirectView(generic.RedirectView):
    permanent = True
    url = reverse('dashboard')


class DashboardView(generic.TemplateView):
    template_name = 'dashboard.html'


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'email',
            'date_of_birth',
            'uses_hormonal_contraception',
            'is_trying_to_conceive'
        )


class SymptomListView(generic.ListView):
    model = Symptom
    template_name = 'symptom_list.html'
    context_object_name = 'symptoms'
    paginate_by = 20
    ordering = 'name'

    def get_queryset(self) -> models.query.QuerySet:
        qs = super().get_queryset()
        query = self.request.GET.get('q', None)
        if query is not None:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(medical_term__icontains=query)
            ).distinct()
        return qs


class SymptomDetailView(generic.DetailView):
    model = Symptom
    template_name = 'symptom_detail.html'
    context_object_name = 'symptom'

    def get_queryset(self) -> models.query.QuerySet:
        return (
            super().get_queryset()
            .select_related('phase')
            .prefetch_related('related')
        )


class PhaseListView(generic.ListView):
    model = Phase
    template_name = 'phase_list.html'
    context_object_name = 'phases'
    ordering = 'name'


class PhaseDetailView(generic.DetailView):
    model = Phase
    template_name = 'phase_detail.html'
    context_object_name = 'phase'

    def get_queryset(self) -> models.query.QuerySet:
        return (
            super().get_queryset()
            .prefetch_related('symptoms')
        )


class DayDetailView(LoginRequiredMixin, UserPassesTestMixin, generic.DetailView):
    model = Day
    template_name = 'day_detail.html'
    context_object_name = 'day'

    def get_queryset(self) -> models.query.QuerySet:
        return (
            super().get_queryset()
            .select_related('phase', 'user')
            .prefetch_related('symptoms')
            .filter(user=self.request.user)
        )

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            self._object = super().get_object(queryset)
        return self._object

    def test_func(self) -> bool:
        return self.request.user == self.get_object().user


class DayCreateView(LoginRequiredMixin, generic.CreateView):
    model = Day
    fields = ('date', 'flow_level', 'symptoms', 'spotting', 'notes',)
    template_name = 'day_create.html'
    context_object_name = 'day'
    success_url = reverse_lazy('calendar')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class DayUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Day
    fields = ('date', 'flow_level', 'symptoms', 'spotting', 'notes',)
    template_name = 'day_update.html'
    context_object_name = 'day'
    success_url = reverse_lazy('calendar')

    def get_queryset(self) -> models.query.QuerySet:
        return (
            super().get_queryset()
            .prefetch_related('symptoms')
            .select_related('user')
            .filter(user=self.request.user)
        )

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            self._object = super().get_object(queryset)
        return self._object

    def test_func(self) -> bool:
        return self.request.user == self.get_object().user


class DayDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Day
    template_name = 'day_delete.html'
    context_object_name = 'day'
    success_url = reverse_lazy('calendar')

    def get_queryset(self) -> models.query.QuerySet:
        return (
            super().get_queryset()
            .select_related('user')
            .filter(user=self.request.user)
        )

    def get_object(self, queryset=None):
        if not hasattr(self, '_object'):
            self._object = super().get_object(queryset)
        return self._object

    def test_func(self) -> bool:
        return self.request.user == self.get_object().user


class CalendarView(LoginRequiredMixin, generic.ListView):
    model = Day
    template_name = 'calendar.html'
    context_object_name = 'days'
    ordering = '-date'

    def get_queryset(self) -> models.query.QuerySet:
        now = timezone.now()
        try:
            month = int(self.request.GET.get('m', now.month))
            year = int(self.request.GET.get('y', now.year))
        except (ValueError, TypeError):
            month, year = now.month, now.year
        if not 1 <= month <= 12:
            month = now.month
        if not 1 <= year <= 9999:
            year = now.year
        return (
            super().get_queryset()
            .select_related('phase')
            .filter(date__month=month, date__year=year, user=self.request.user)
        )


class SettingsView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = User
    fields = (
        'email',
        'date_of_birth',
        'uses_hormonal_contraception',
        'is_trying_to_conceive'
    )
    template_name = 'settings_update.html'
    context_object_name = 'user'
    success_url = reverse_lazy('calendar')

    def get_object(self, queryset=None):
        return self.request.user

    def test_func(self) -> bool:
        return self.request.user == self.get_object()


class RegisterView(generic.CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')
