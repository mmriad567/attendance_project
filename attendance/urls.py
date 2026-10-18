from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path(
        "offering/<int:pk>/session/new/",
        views.SessionCreateView.as_view(),
        name="session_create",
    ),
    path(
        "session/<int:pk>/mark/",
        views.SessionMarkView.as_view(),
        name="session_mark",
    ),
    path(
        "session/<int:pk>/record/<int:student_pk>/set/",
        views.RecordSetView.as_view(),
        name="record_set",
    ),
    path(
        "session/<int:pk>/present-all/",
        views.MarkAllPresentView.as_view(),
        name="mark_all_present",
    ),
]
