from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.tests.base import BaseTestCase
from attendance.models import AttendanceStatus
from attendance.services import create_class_session
from attendance.tests.factories import build_offering

User = get_user_model()


class StudentViewTestMixin:
    def setUp(self):
        self.fx = build_offering(num_students=1, code="28531")
        self.student = self.fx.students[0]
        self.student_user = self.student.user
        self.teacher = self.fx.teacher

    def _record(self, period, status):
        session = create_class_session(
            offering=self.fx.offering,
            date=timezone.localdate(),
            period_no=period,
            created_by=self.teacher,
        )
        session.records.filter(student=self.student).update(status=status)
        return session


class DashboardViewTests(StudentViewTestMixin, BaseTestCase):
    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("students:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_teacher_forbidden(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("students:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_student_sees_own_percentage(self):
        self._record(1, AttendanceStatus.PRESENT)
        self._record(2, AttendanceStatus.ABSENT)
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("students:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "50.0%")
        self.assertContains(response, self.student.roll_no)

    def test_low_attendance_warning_shown(self):
        for period in range(1, 4):
            self._record(period, AttendanceStatus.ABSENT)
        self._record(4, AttendanceStatus.PRESENT)
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("students:dashboard"))
        self.assertContains(response, "Low attendance warning")

    def test_student_without_profile_gets_404(self):
        orphan = User.objects.create_user(
            username="orphan", password="pw12345!", role=Role.STUDENT
        )
        self.client.force_login(orphan)
        response = self.client.get(reverse("students:dashboard"))
        self.assertEqual(response.status_code, 404)


class HistoryViewTests(StudentViewTestMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self._record(1, AttendanceStatus.PRESENT)
        self._record(2, AttendanceStatus.ABSENT)
        self.client.force_login(self.student_user)

    def test_lists_records(self):
        response = self.client.get(reverse("students:history"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["records"]), 2)

    def test_filter_by_status(self):
        response = self.client.get(
            reverse("students:history"), {"status": AttendanceStatus.PRESENT}
        )
        records = list(response.context["records"])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].status, AttendanceStatus.PRESENT)

    def test_does_not_show_other_students(self):
        # A second student in a different offering must not leak in.
        fx2 = build_offering(num_students=1, code="28532")
        create_class_session(
            offering=fx2.offering,
            date=timezone.localdate(),
            period_no=1,
            created_by=fx2.teacher,
        )
        response = self.client.get(reverse("students:history"))
        self.assertEqual(len(response.context["records"]), 2)
