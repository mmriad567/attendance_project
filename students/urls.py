from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("history/", views.HistoryView.as_view(), name="history"),
]
