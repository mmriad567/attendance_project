from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View

from academics.models import SubjectOffering
from accounts.mixins import RoleRequiredMixin
from accounts.models import Role

from .forms import ClassSessionForm
from .models import AttendanceStatus, ClassSession
from .services import create_class_session


class TeacherRequiredMixin(RoleRequiredMixin):
    allowed_roles = (Role.TEACHER, Role.ADMIN)


class DashboardView(TeacherRequiredMixin, TemplateView):
    template_name = "attendance/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offerings = (
            SubjectOffering.objects.filter(teacher=self.request.user)
            .select_related("subject", "session")
            .order_by("subject__code")
        )
        context["offerings"] = offerings
        context["today"] = timezone.localdate()
        context["todays_sessions"] = (
            ClassSession.objects.filter(
                offering__teacher=self.request.user, date=timezone.localdate()
            )
            .select_related("offering__subject")
            .order_by("period_no")
        )
        return context


class SessionCreateView(TeacherRequiredMixin, View):
    def get_offering(self, request, pk):
        return get_object_or_404(SubjectOffering, pk=pk, teacher=request.user)

    def get(self, request, pk):
        offering = self.get_offering(request, pk)
        form = ClassSessionForm(offering=offering, initial={"date": timezone.localdate()})
        return self._render(request, offering, form)

    def post(self, request, pk):
        offering = self.get_offering(request, pk)
        form = ClassSessionForm(request.POST, offering=offering)
        if form.is_valid():
            session = create_class_session(
                offering=offering, created_by=request.user, **form.cleaned_data
            )
            mark_url = reverse("attendance:session_mark", args=[session.pk])
            if request.headers.get("HX-Request"):
                response = HttpResponse(status=204)
                response["HX-Redirect"] = mark_url
                return response
            return redirect(mark_url)
        return self._render(request, offering, form)

    def _render(self, request, offering, form):
        template = (
            "attendance/partials/_session_form.html"
            if request.headers.get("HX-Request")
            else "attendance/session_form.html"
        )
        return render(request, template, {"offering": offering, "form": form})


class SessionMarkView(TeacherRequiredMixin, TemplateView):
    template_name = "attendance/session_mark.html"

    def get_session(self):
        return get_object_or_404(
            ClassSession.objects.select_related(
                "offering__subject", "offering__session"
            ),
            pk=self.kwargs["pk"],
            offering__teacher=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.get_session()
        context["session"] = session
        context["records"] = session.records.select_related("student__user")
        context["statuses"] = AttendanceStatus.choices
        context["editable"] = session.is_editable
        return context


class RecordSetView(TeacherRequiredMixin, View):
    """HTMX endpoint: set one student's status and return the updated row."""

    def post(self, request, pk, student_pk):
        session = get_object_or_404(
            ClassSession, pk=pk, offering__teacher=request.user
        )
        if not session.is_editable:
            return HttpResponse("Editing window has closed.", status=403)

        status = request.POST.get("status")
        if status not in AttendanceStatus.values:
            return HttpResponse("Invalid status.", status=400)

        record = get_object_or_404(
            session.records, student_id=student_pk
        )
        record.mark(status, request.user)
        return render(
            request,
            "attendance/partials/_student_row.html",
            {"session": session, "record": record, "statuses": AttendanceStatus.choices, "editable": True},
        )


class MarkAllPresentView(TeacherRequiredMixin, View):
    """HTMX endpoint: mark every student in the session present."""

    def post(self, request, pk):
        session = get_object_or_404(
            ClassSession, pk=pk, offering__teacher=request.user
        )
        if not session.is_editable:
            return HttpResponse("Editing window has closed.", status=403)

        session.records.update(
            status=AttendanceStatus.PRESENT,
            marked_by=request.user,
            marked_at=timezone.now(),
            updated_at=timezone.now(),
        )
        return render(
            request,
            "attendance/partials/_records_table.html",
            {
                "session": session,
                "records": session.records.select_related("student__user"),
                "statuses": AttendanceStatus.choices,
                "editable": True,
            },
        )
