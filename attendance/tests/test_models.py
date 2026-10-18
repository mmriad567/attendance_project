from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.tests.base import BaseTestCase

from .factories import build_offering
from ..models import AttendanceRecord, AttendanceStatus, ClassSession, edit_window_days


class ClassSessionTests(BaseTestCase):
    def setUp(self):
        fixture = build_offering()
        self.offering = fixture.offering
        self.teacher = fixture.teacher

    def _session(self, date, period=1):
        return ClassSession.objects.create(
            offering=self.offering,
            date=date,
            period_no=period,
            created_by=self.teacher,
        )

    def test_is_editable_within_window(self):
        today = timezone.localdate()
        self.assertTrue(self._session(today, 1).is_editable)
        self.assertTrue(
            self._session(today - timedelta(days=edit_window_days()), 2).is_editable
        )

    def test_is_not_editable_past_window(self):
        old = timezone.localdate() - timedelta(days=edit_window_days() + 1)
        self.assertFalse(self._session(old, 3).is_editable)

    def test_unique_per_offering_date_period(self):
        today = timezone.localdate()
        self._session(today, 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._session(today, 1)

    def test_different_period_allowed(self):
        today = timezone.localdate()
        self._session(today, 1)
        self.assertEqual(self._session(today, 2).period_no, 2)


class AttendanceRecordTests(BaseTestCase):
    def setUp(self):
        fixture = build_offering(num_students=2)
        self.session = ClassSession.objects.create(
            offering=fixture.offering,
            date=timezone.localdate(),
            period_no=1,
            created_by=fixture.teacher,
        )
        self.student = fixture.students[0]
        self.record = AttendanceRecord.objects.create(
            class_session=self.session, student=self.student
        )

    def test_default_status_is_absent(self):
        self.assertEqual(self.record.status, AttendanceStatus.ABSENT)

    def test_mark_sets_status_and_audit_fields(self):
        teacher = self.session.offering.teacher
        self.record.mark(AttendanceStatus.PRESENT, teacher)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, AttendanceStatus.PRESENT)
        self.assertEqual(self.record.marked_by, teacher)
        self.assertIsNotNone(self.record.marked_at)

    def test_unique_record_per_session_student(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AttendanceRecord.objects.create(
                class_session=self.session, student=self.student
            )
