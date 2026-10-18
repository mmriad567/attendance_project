from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.tests.base import BaseTestCase
from attendance.models import AttendanceStatus
from attendance.services import create_class_session
from attendance.tests.factories import build_offering

User = get_user_model()


class ReportTestMixin:
    def setUp(self):
        self.fx = build_offering(num_students=2, code="28531")
        self.offering = self.fx.offering
        self.teacher = self.fx.teacher
        self.good, self.bad = self.fx.students
        self.today = timezone.localdate()
        for period in range(1, 4):
            session = create_class_session(
                offering=self.offering,
                date=self.today,
                period_no=period,
                created_by=self.teacher,
            )
            session.records.filter(student=self.good).update(
                status=AttendanceStatus.PRESENT
            )
            session.records.filter(student=self.bad).update(
                status=AttendanceStatus.ABSENT
            )


class OfferingListViewTests(ReportTestMixin, BaseTestCase):
    def test_anonymous_redirected(self):
        response = self.client.get(reverse("reports:offering_list"))
        self.assertEqual(response.status_code, 302)

    def test_student_forbidden(self):
        self.client.force_login(self.good.user)
        response = self.client.get(reverse("reports:offering_list"))
        self.assertEqual(response.status_code, 403)

    def test_teacher_sees_own_offering(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("reports:offering_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "28531")


class OfferingReportViewTests(ReportTestMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_report_renders_metrics(self):
        response = self.client.get(
            reverse("reports:offering_report", args=[self.offering.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.good.roll_no)
        self.assertContains(response, "50.0%")  # average of 100% and 0%

    def test_other_teacher_gets_404(self):
        other = User.objects.create_user(
            username="other", password="pw12345!", role=Role.TEACHER
        )
        self.client.force_login(other)
        response = self.client.get(
            reverse("reports:offering_report", args=[self.offering.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_defaulters_list(self):
        response = self.client.get(reverse("reports:defaulters", args=[self.offering.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.bad.roll_no)


class ExportViewTests(ReportTestMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)

    def test_csv_export(self):
        response = self.client.get(reverse("reports:offering_csv", args=[self.offering.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])
        body = response.content.decode()
        self.assertIn("Roll", body)
        self.assertIn(self.good.roll_no, body)

    def test_pdf_export(self):
        response = self.client.get(reverse("reports:offering_pdf", args=[self.offering.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
