from django.shortcuts import get_object_or_404
from django.views.generic import ListView, TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import Role, StudentProfile
from attendance.models import AttendanceRecord, AttendanceStatus
from attendance.services import student_summary


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = (Role.STUDENT,)

    def get_student(self):
        return get_object_or_404(StudentProfile, user=self.request.user)


class DashboardView(StudentRequiredMixin, TemplateView):
    template_name = "students/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = student_summary(self.get_student())
        return context


class HistoryView(StudentRequiredMixin, ListView):
    template_name = "students/history.html"
    context_object_name = "records"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            AttendanceRecord.objects.filter(student=self.get_student())
            .select_related(
                "class_session__offering__subject", "class_session__offering__session"
            )
            .order_by("-class_session__date", "-class_session__period_no")
        )
        offering_id = self.request.GET.get("offering")
        if offering_id:
            qs = qs.filter(class_session__offering_id=offering_id)
        status = self.request.GET.get("status")
        if status in AttendanceStatus.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_student()
        context["offerings"] = (
            student.enrollments.filter(is_active=True)
            .select_related("offering__subject")
            .order_by("offering__subject__code")
        )
        context["statuses"] = AttendanceStatus.choices
        context["filters"] = {
            "offering": self.request.GET.get("offering", ""),
            "status": self.request.GET.get("status", ""),
        }
        return context
