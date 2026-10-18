from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.tests.base import BaseTestCase
from attendance.models import AttendanceRecord, AttendanceStatus, ClassSession
from attendance.services import create_class_session

from .factories import build_offering

User = get_user_model()


class AttendanceViewTestMixin:
    def setUp(self):
        self.fixture = build_offering(num_students=3, code="28531")
        self.teacher = self.fixture.teacher
        self.offering = self.fixture.offering
        self.students = self.fixture.students

    def _make_session(self, *, date=None, period=1, teacher=None):
        return ClassSession.objects.create(
            offering=self.offering,
            date=date or timezone.localdate(),
            period_no=period,
            created_by=teacher or self.teacher,
        )


class DashboardViewTests(AttendanceViewTestMixin, BaseTestCase):
    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("attendance:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_student_forbidden(self):
        student_user = self.students[0].user
        self.client.force_login(student_user)
        response = self.client.get(reverse("attendance:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_teacher_sees_offerings(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("attendance:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "28531")


class SessionCreateViewTests(AttendanceViewTestMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.teacher)
        self.url = reverse("attendance:session_create", args=[self.offering.pk])

    def test_get_returns_partial_for_htmx(self):
        response = self.client.get(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "attendance/partials/_session_form.html")

    def test_post_creates_session_and_records(self):
        response = self.client.post(
            self.url,
            {"date": timezone.localdate().isoformat(), "period_no": 2, "topic": "Loops"},
        )
        session = ClassSession.objects.get(offering=self.offering, period_no=2)
        self.assertEqual(session.records.count(), 3)
        self.assertRedirects(
            response, reverse("attendance:session_mark", args=[session.pk])
        )

    def test_post_htmx_returns_hx_redirect(self):
        response = self.client.post(
            self.url,
            {"date": timezone.localdate().isoformat(), "period_no": 3},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 204)
        session = ClassSession.objects.get(offering=self.offering, period_no=3)
        self.assertEqual(
            response["HX-Redirect"], reverse("attendance:session_mark", args=[session.pk])
        )

    def test_duplicate_session_returns_form_error(self):
        today = timezone.localdate().isoformat()
        self.client.post(self.url, {"date": today, "period_no": 1})
        response = self.client.post(
            self.url, {"date": today, "period_no": 1}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_future_date_rejected(self):
        future = (timezone.localdate() + timedelta(days=1)).isoformat()
        response = self.client.post(self.url, {"date": future, "period_no": 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "future date")

    def test_cannot_create_for_other_teacher_offering(self):
        other = User.objects.create_user(
            username="other", password="pw12345!", role=Role.TEACHER
        )
        self.client.force_login(other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class SessionMarkViewTests(AttendanceViewTestMixin, BaseTestCase):
    def _session_with_records(self):
        return create_class_session(
            offering=self.offering,
            date=timezone.localdate(),
            period_no=2,
            created_by=self.teacher,
        )

    def test_teacher_sees_students(self):
        session = self._session_with_records()
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("attendance:session_mark", args=[session.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.students[0].roll_no)

    def test_other_teacher_gets_404(self):
        session = self._session_with_records()
        other = User.objects.create_user(
            username="other2", password="pw12345!", role=Role.TEACHER
        )
        self.client.force_login(other)
        response = self.client.get(reverse("attendance:session_mark", args=[session.pk]))
        self.assertEqual(response.status_code, 404)


class RecordSetViewTests(AttendanceViewTestMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.session = self._make_session()
        self.student = self.students[0]
        self.record = AttendanceRecord.objects.create(
            class_session=self.session, student=self.student
        )
        self.client.force_login(self.teacher)
        self.url = reverse(
            "attendance:record_set", args=[self.session.pk, self.student.pk]
        )

    def test_sets_status_and_returns_row(self):
        response = self.client.post(
            self.url, {"status": AttendanceStatus.PRESENT}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, AttendanceStatus.PRESENT)
        self.assertContains(response, f"record-{self.student.pk}")

    def test_invalid_status_rejected(self):
        response = self.client.post(self.url, {"status": "nonsense"})
        self.assertEqual(response.status_code, 400)

    def test_closed_window_forbidden(self):
        old = timezone.localdate() - timedelta(days=10)
        session = self._make_session(date=old, period=5)
        record = AttendanceRecord.objects.create(
            class_session=session, student=self.student
        )
        url = reverse("attendance:record_set", args=[session.pk, self.student.pk])
        response = self.client.post(url, {"status": AttendanceStatus.PRESENT})
        self.assertEqual(response.status_code, 403)
        record.refresh_from_db()
        self.assertEqual(record.status, AttendanceStatus.ABSENT)


class MarkAllPresentViewTests(AttendanceViewTestMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.session = self._make_session()
        for student in self.students:
            AttendanceRecord.objects.create(
                class_session=self.session, student=student
            )
        self.client.force_login(self.teacher)

    def test_marks_everyone_present(self):
        response = self.client.post(
            reverse("attendance:mark_all_present", args=[self.session.pk]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.session.records.filter(status=AttendanceStatus.PRESENT).count(), 3
        )
