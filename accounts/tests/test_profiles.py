from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from accounts.models import (
    AcademicSession,
    Department,
    Designation,
    Role,
    Shift,
    StudentProfile,
    TeacherProfile,
)

from .base import BaseTestCase

User = get_user_model()


class ProfileTestMixin:
    def setUp(self):
        self.cst = Department.objects.create(code="CST", name="Computer Science and Technology")
        self.eee = Department.objects.create(code="EEE", name="Electrical and Electronics")
        self.session = AcademicSession.objects.create(name="2022-2023")

    def _student_user(self, username):
        return User.objects.create_user(
            username=username, password="pw12345!", role=Role.STUDENT
        )

    def _make_student(self, username, roll, department=None, session=None, **extra):
        defaults = {
            "roll_no": roll,
            "department": department or self.cst,
            "session": session or self.session,
        }
        defaults.update(extra)
        return StudentProfile.objects.create(user=self._student_user(username), **defaults)


class DepartmentTests(ProfileTestMixin, BaseTestCase):
    def test_str(self):
        self.assertEqual(str(self.cst), "CST - Computer Science and Technology")

    def test_code_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Department.objects.create(code="CST", name="Duplicate")


class StudentProfileTests(ProfileTestMixin, BaseTestCase):
    def test_create_and_str(self):
        profile = self._make_student("s1", "2022001")
        self.assertEqual(profile.shift, Shift.FIRST)
        self.assertEqual(profile.status, "active")
        self.assertIn("2022001", str(profile))

    def test_roll_unique_within_session_and_department(self):
        self._make_student("s1", "2022001")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._make_student("s2", "2022001")

    def test_same_roll_allowed_in_different_department(self):
        self._make_student("s1", "2022001", department=self.cst)
        profile = self._make_student("s2", "2022001", department=self.eee)
        self.assertEqual(profile.department, self.eee)

    def test_registration_no_is_unique(self):
        self._make_student("s1", "2022001", registration_no="REG-1")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._make_student("s2", "2022002", registration_no="REG-1")

    def test_semester_validator_rejects_out_of_range(self):
        profile = self._make_student("s1", "2022001", current_semester=9)
        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_user_one_to_one(self):
        user = self._student_user("s1")
        StudentProfile.objects.create(user=user, roll_no="2022001", department=self.cst, session=self.session)
        with self.assertRaises(IntegrityError), transaction.atomic():
            StudentProfile.objects.create(user=user, roll_no="2022002", department=self.cst, session=self.session)


class TeacherProfileTests(ProfileTestMixin, BaseTestCase):
    def _teacher_user(self, username):
        return User.objects.create_user(
            username=username, password="pw12345!", role=Role.TEACHER
        )

    def test_create_and_str(self):
        profile = TeacherProfile.objects.create(
            user=self._teacher_user("t1"),
            employee_id="EMP-001",
            department=self.cst,
            designation=Designation.JUNIOR_INSTRUCTOR,
        )
        self.assertIn("EMP-001", str(profile))

    def test_employee_id_unique(self):
        TeacherProfile.objects.create(
            user=self._teacher_user("t1"), employee_id="EMP-001", department=self.cst
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            TeacherProfile.objects.create(
                user=self._teacher_user("t2"), employee_id="EMP-001", department=self.cst
            )
