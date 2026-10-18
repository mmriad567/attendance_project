import csv

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from academics.models import SubjectOffering
from accounts.mixins import RoleRequiredMixin
from accounts.models import Role
from attendance.services import (
    offering_status_distribution,
    offering_student_rows,
    offering_trends,
)

from .pdf import build_offering_pdf


class ReportAccessMixin(RoleRequiredMixin):
    allowed_roles = (Role.TEACHER, Role.ADMIN)

    def accessible_offerings(self):
        qs = SubjectOffering.objects.select_related("subject", "session")
        if self.request.user.is_admin:
            return qs
        return qs.filter(teacher=self.request.user)

    def get_offering(self, pk):
        return get_object_or_404(self.accessible_offerings(), pk=pk)


class OfferingListView(ReportAccessMixin, TemplateView):
    template_name = "reports/offering_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["offerings"] = self.accessible_offerings().order_by("subject__code")
        return context


class OfferingReportView(ReportAccessMixin, TemplateView):
    template_name = "reports/offering_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offering = self.get_offering(self.kwargs["pk"])
        rows = offering_student_rows(offering)
        trends = offering_trends(offering)
        distribution = offering_status_distribution(offering)
        percentages = [row["percentage"] for row in rows if row["percentage"] is not None]

        context["offering"] = offering
        context["rows"] = rows
        context["defaulters"] = [row for row in rows if row["below_threshold"]]
        context["distribution"] = distribution
        context["trends"] = trends
        context["threshold"] = getattr(settings, "ATTENDANCE_THRESHOLD", 60)
        context["student_labels"] = [row["student"].roll_no for row in rows]
        context["student_percentages"] = [row["percentage"] or 0 for row in rows]
        context["trend_labels"] = [point["label"] for point in trends]
        context["trend_percentages"] = [point["percentage"] for point in trends]
        context["average_percentage"] = (
            round(sum(percentages) / len(percentages), 1) if percentages else None
        )
        return context


class OfferingCSVView(ReportAccessMixin, TemplateView):
    def get(self, request, pk):
        offering = self.get_offering(pk)
        rows = offering_student_rows(offering)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{offering.subject.code}-attendance.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            ["Roll", "Name", "Present", "Late", "Absent", "Excused", "Attended", "Total", "Percentage"]
        )
        for row in rows:
            name = row["student"].user.get_full_name() or row["student"].user.username
            writer.writerow(
                [
                    row["student"].roll_no,
                    name,
                    row["present"],
                    row["late"],
                    row["absent"],
                    row["excused"],
                    row["attended"],
                    row["total"],
                    "" if row["percentage"] is None else row["percentage"],
                ]
            )
        return response


class OfferingPDFView(ReportAccessMixin, TemplateView):
    def get(self, request, pk):
        offering = self.get_offering(pk)
        rows = offering_student_rows(offering)

        pdf_bytes = build_offering_pdf(offering, rows)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{offering.subject.code}-attendance.pdf"'
        )
        return response


class DefaulterListView(ReportAccessMixin, TemplateView):
    template_name = "reports/defaulters.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offering = self.get_offering(self.kwargs["pk"])
        rows = offering_student_rows(offering)
        context["offering"] = offering
        context["defaulters"] = [row for row in rows if row["below_threshold"]]
        return context
