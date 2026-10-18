from django.utils import timezone

from accounts.tests.base import BaseTestCase

from .factories import build_offering
from ..models import AttendanceRecord, AttendanceStatus
from ..services import create_class_session


class CreateClassSessionTests(BaseTestCase):
    def setUp(self):
        self.fixture = build_offering(num_students=4)

    def test_creates_session_with_records_for_each_enrolled_student(self):
        session = create_class_session(
            offering=self.fixture.offering,
            date=timezone.localdate(),
            period_no=2,
            created_by=self.fixture.teacher,
            topic="Intro",
        )
        self.assertEqual(session.records.count(), 4)
        self.assertTrue(
            all(r.status == AttendanceStatus.ABSENT for r in session.records.all())
        )
        self.assertEqual(session.created_by, self.fixture.teacher)

    def test_records_link_to_correct_students(self):
        session = create_class_session(
            offering=self.fixture.offering,
            date=timezone.localdate(),
            period_no=3,
            created_by=self.fixture.teacher,
        )
        recorded = set(
            AttendanceRecord.objects.filter(class_session=session).values_list(
                "student_id", flat=True
            )
        )
        expected = {student.pk for student in self.fixture.students}
        self.assertEqual(recorded, expected)
