from django.utils import timezone

from academics.models import Enrollment
from accounts.tests.base import BaseTestCase
from attendance.models import AttendanceStatus
from attendance.services import create_class_session, offering_stats, student_summary
from attendance.tests.factories import build_offering


class OfferingStatsTests(BaseTestCase):
    def setUp(self):
        self.fx = build_offering(num_students=1, code="28531")
        self.student = self.fx.students[0]
        self.offering = self.fx.offering
        self.teacher = self.fx.teacher
        self.today = timezone.localdate()

    def _session(self, period, status):
        session = create_class_session(
            offering=self.offering,
            date=self.today,
            period_no=period,
            created_by=self.teacher,
        )
        session.records.update(status=status)
        return session

    def test_percentage_counts_present_and_late_as_attended(self):
        self._session(1, AttendanceStatus.PRESENT)
        self._session(2, AttendanceStatus.PRESENT)
        self._session(3, AttendanceStatus.PRESENT)
        self._session(4, AttendanceStatus.LATE)
        self._session(5, AttendanceStatus.ABSENT)

        stats = offering_stats(self.student, self.offering, threshold=75)

        self.assertEqual(stats["total"], 5)
        self.assertEqual(stats["present"], 3)
        self.assertEqual(stats["late"], 1)
        self.assertEqual(stats["absent"], 1)
        self.assertEqual(stats["attended"], 4)
        self.assertEqual(stats["percentage"], 80.0)
        self.assertFalse(stats["below_threshold"])

    def test_no_records_gives_none_percentage(self):
        stats = offering_stats(self.student, self.offering)
        self.assertEqual(stats["total"], 0)
        self.assertIsNone(stats["percentage"])
        self.assertFalse(stats["below_threshold"])

    def test_below_threshold_flag(self):
        self._session(1, AttendanceStatus.PRESENT)
        self._session(2, AttendanceStatus.ABSENT)
        self._session(3, AttendanceStatus.ABSENT)
        self._session(4, AttendanceStatus.ABSENT)

        stats = offering_stats(self.student, self.offering, threshold=60)
        self.assertEqual(stats["percentage"], 25.0)
        self.assertTrue(stats["below_threshold"])

    def test_other_students_records_are_ignored(self):
        # A second student in the same offering must not affect the first.
        fx2 = build_offering(num_students=1, code="28532")
        self.offering = fx2.offering
        self.student = fx2.students[0]
        session = create_class_session(
            offering=self.offering,
            date=self.today,
            period_no=1,
            created_by=fx2.teacher,
        )
        session.records.filter(student=self.student).update(
            status=AttendanceStatus.PRESENT
        )
        stats = offering_stats(self.student, self.offering)
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["percentage"], 100.0)


class StudentSummaryTests(BaseTestCase):
    def setUp(self):
        self.fx = build_offering(num_students=1, code="28531")
        self.student = self.fx.students[0]
        self.teacher = self.fx.teacher
        self.today = timezone.localdate()

    def _mark_offering(self, offering, statuses, created_by):
        for period, status in enumerate(statuses, start=1):
            session = create_class_session(
                offering=offering, date=self.today, period_no=period, created_by=created_by
            )
            session.records.filter(student=self.student).update(status=status)

    def test_aggregates_across_offerings(self):
        # Offering 1: 2 present, 1 absent -> 2/3
        self._mark_offering(
            self.fx.offering,
            [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.ABSENT],
            self.teacher,
        )
        # Offering 2 shares the same student.
        fx2 = build_offering(num_students=0, code="28532")
        Enrollment.objects.create(student=self.student, offering=fx2.offering)
        self._mark_offering(
            fx2.offering,
            [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT],
            fx2.teacher,
        )

        summary = student_summary(self.student, threshold=60)

        self.assertEqual(len(summary["rows"]), 2)
        self.assertEqual(summary["total"], 5)
        self.assertEqual(summary["attended"], 3)
        self.assertEqual(summary["percentage"], 60.0)

    def test_low_offerings_listed(self):
        self._mark_offering(
            self.fx.offering,
            [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.ABSENT],
            self.teacher,
        )
        summary = student_summary(self.student, threshold=60)
        self.assertEqual(len(summary["low_offerings"]), 1)

    def test_inactive_enrollment_excluded(self):
        Enrollment.objects.filter(student=self.student).update(is_active=False)
        summary = student_summary(self.student)
        self.assertEqual(summary["rows"], [])
        self.assertEqual(summary["total"], 0)
        self.assertIsNone(summary["percentage"])
