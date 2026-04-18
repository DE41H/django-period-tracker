from django.urls import path
from cycle.views import (
    DashboardRedirectView,
    DashboardView,
    SymptomListView,
    SymptomDetailView,
    PhaseListView,
    PhaseDetailView,
    DayDetailView,
    DayCreateView,
    DayUpdateView,
    DayDeleteView,
    CalendarView,
    SettingsView,
    RegisterView,
)

urlpatterns = [
    path('', DashboardRedirectView.as_view()),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('symptoms/', SymptomListView.as_view(), name='symptom_list'),
    path('symptoms/<int:pk>/', SymptomDetailView.as_view(), name='symptom_detail'),
    path('phases/', PhaseListView.as_view(), name='phase_list'),
    path('phases/<int:pk>/', PhaseDetailView.as_view(), name='phase_detail'),
    path('days/<int:pk>/', DayDetailView.as_view(), name='day_detail'),
    path('days/create/', DayCreateView.as_view(), name='day_create'),
    path('days/<int:pk>/update/', DayUpdateView.as_view(), name='day_update'),
    path('days/<int:pk>/delete/', DayDeleteView.as_view(), name='day_delete'),
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('register/', RegisterView.as_view(), name='register'),
]
