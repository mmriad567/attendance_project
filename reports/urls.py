from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.OfferingListView.as_view(), name="offering_list"),
    path("offering/<int:pk>/", views.OfferingReportView.as_view(), name="offering_report"),
    path("offering/<int:pk>/export/csv/", views.OfferingCSVView.as_view(), name="offering_csv"),
    path("offering/<int:pk>/export/pdf/", views.OfferingPDFView.as_view(), name="offering_pdf"),
    path("offering/<int:pk>/defaulters/", views.DefaulterListView.as_view(), name="defaulters"),
]
