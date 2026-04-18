import calendar as cal_module

from django.db import models
from django.db.models import Q
from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone

from cycle.models import Phase, Symptom, Day, User, FlowLevel
from cycle.forms import CustomUserCreationForm, DayLogForm


class DashboardRedirectView(generic.RedirectView):
    permanent = True
    pattern_name = 'dashboard'


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        # Last actual (non-predicted) period start
        last_period = (
            Day.objects
            .filter(user=user, prediction=False)
            .exclude(flow_level=FlowLevel.NONE)
            .order_by('-date')
            .first()
        )

        cycle_day = (today - last_period.date).days + 1 if last_period else None
        cycle_length = max(21, round(user.kalman_estimate))  # pyright: ignore[reportAttributeAccessIssue]

        # Today's logged entry
        today_day = (
            Day.objects
            .filter(user=user, date=today)
            .select_related('phase')
            .prefetch_related('symptoms')
            .first()
        )

        # Next predicted period
        next_period = (
            Day.objects
            .filter(user=user, prediction=True, date__gt=today)
            .exclude(flow_level=FlowLevel.NONE)
            .order_by('date')
            .first()
        )
        days_until_period = (next_period.date - today).days if next_period else None

        # Next fertile window start
        next_fertile = (
            Day.objects
            .filter(user=user, prediction=True, fertile=True, date__gte=today)
            .order_by('date')
            .first()
        )
        # End of that fertile window
        next_fertile_end = None
        if next_fertile:
            next_fertile_end = (
                Day.objects
                .filter(user=user, prediction=True, fertile=True,
                        date__gte=next_fertile.date)
                .order_by('-date')
                .first()
            )

        # Current phase from today's prediction if not logged
        predicted_today = (
            Day.objects
            .filter(user=user, date=today, prediction=True)
            .select_related('phase')
            .first()
        ) if not today_day else None
        current_phase = (
            (today_day.phase if today_day else None)
            or (predicted_today.phase if predicted_today else None)
        )

        # Recent logged days (non-prediction)
        recent_days = list(
            Day.objects
            .filter(user=user, prediction=False)
            .select_related('phase')
            .prefetch_related('symptoms')
            .order_by('-date')[:5]
        )

        ctx.update({
            'today': today,
            'cycle_day': cycle_day,
            'cycle_length': cycle_length,
            'last_period': last_period,
            'next_period': next_period,
            'days_until_period': days_until_period,
            'today_day': today_day,
            'current_phase': current_phase,
            'next_fertile': next_fertile,
            'next_fertile_end': next_fertile_end,
            'recent_days': recent_days,
            'kalman_estimate': round(user.kalman_estimate, 1),  # pyright: ignore[reportAttributeAccessIssue]
        })
        return ctx


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
    ordering = 'typical_start_day'


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
    form_class = DayLogForm
    template_name = 'day_create.html'
    context_object_name = 'day'
    success_url = reverse_lazy('calendar')

    def get_initial(self):
        initial = super().get_initial()
        initial['date'] = timezone.now().date()
        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class DayUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Day
    form_class = DayLogForm
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

    def _parse_month_year(self):
        now = timezone.now()
        try:
            month = int(self.request.GET.get('m', now.month))
            year = int(self.request.GET.get('y', now.year))
        except (ValueError, TypeError):
            return now.month, now.year
        if not 1 <= month <= 12:
            month = now.month
        if not 1 <= year <= 9999:
            year = now.year
        return month, year

    def get_queryset(self) -> models.query.QuerySet:
        month, year = self._parse_month_year()
        return (
            super().get_queryset()
            .select_related('phase')
            .filter(date__month=month, date__year=year, user=self.request.user)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        month, year = self._parse_month_year()
        now = timezone.now()

        days_dict = {d.date.day: d for d in ctx['days']}

        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year
        next_month = 1 if month == 12 else month + 1
        next_year = year + 1 if month == 12 else year

        ctx.update({
            'month': month,
            'year': year,
            'month_name': cal_module.month_name[month],
            'calendar_weeks': cal_module.monthcalendar(year, month),
            'days_dict': days_dict,
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'today': now.date(),
        })
        return ctx


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
    success_url = reverse_lazy('settings')

    def get_object(self, queryset=None):
        return self.request.user

    def test_func(self) -> bool:
        return self.request.user == self.get_object()


class RegisterView(generic.CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')
