from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from academics.models import Enrollment, Subject, SubjectOffering, SubjectType
from accounts.models import AcademicSession, Department, Role, Shift, StudentProfile
from accounts.tests.base import BaseTestCase

User = get_user_model()


class AcademicsTestMixin:
    def setUp(self):
        self.cst = Department.objects.create(code="CST", name="Computer Science and Technology")
        self.session = AcademicSession.objects.create(name="2022-2023")
        self.teacher = User.objects.create_user(
            username="teacher1", password="pw12345!", role=Role.TEACHER
        )

    def _subject(self, code="28531", **extra):
        defaults = {
            "name": "Object Oriented Programming",
            "department": self.cst,
            "semester": 3,
            "subject_type": SubjectType.THEORY,
            "credit": 3.0,
        }
        defaults.update(extra)
        return Subject.objects.create(code=code, **defaults)

    def _offering(self, subject, **extra):
        defaults = {
            "session": self.session,
            "semester": 3,
            "shift": Shift.FIRST,
            "section": "A",
            "teacher": self.teacher,
        }
        defaults.update(extra)
        return SubjectOffering.objects.create(subject=subject, **defaults)


class SubjectTests(AcademicsTestMixin, BaseTestCase):
    def test_str_and_defaults(self):
        subject = self._subject()
        self.assertEqual(str(subject), "28531 - Object Oriented Programming")
        self.assertTrue(subject.is_active)
        self.assertEqual(subject.weekly_classes, 1)

    def test_code_unique(self):
        self._subject(code="28531")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._subject(code="28531", name="Another")

    def test_semester_validator(self):
        subject = self._subject(code="99999", semester=9)
        with self.assertRaises(ValidationError):
            subject.full_clean()


class SubjectOfferingTests(AcademicsTestMixin, BaseTestCase):
    def test_str(self):
        offering = self._offering(self._subject())
        self.assertIn("28531", str(offering))
        self.assertIn("2022-2023", str(offering))

    def test_unique_per_subject_session_semester_shift_section(self):
        subject = self._subject()
        self._offering(subject)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._offering(subject)

    def test_different_section_allowed(self):
        subject = self._subject()
        self._offering(subject, section="A")
        offering = self._offering(subject, section="B")
        self.assertEqual(offering.section, "B")


class EnrollmentTests(AcademicsTestMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.offering = self._offering(self._subject())
        user = User.objects.create_user(username="stu1", password="pw12345!", role=Role.STUDENT)
        self.student = StudentProfile.objects.create(
            user=user, roll_no="2022001", department=self.cst, session=self.session
        )

    def test_create_and_str(self):
        enrollment = Enrollment.objects.create(student=self.student, offering=self.offering)
        self.assertIn("2022001", str(enrollment))
        self.assertTrue(enrollment.is_active)

    def test_unique_student_offering(self):
        Enrollment.objects.create(student=self.student, offering=self.offering)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Enrollment.objects.create(student=self.student, offering=self.offering)
