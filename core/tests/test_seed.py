from django.core.management import call_command

from academics.models import Enrollment, Subject, SubjectOffering
from accounts.models import StudentProfile, TeacherProfile
from accounts.tests.base import BaseTestCase
from core.models import SystemSetting


class SeedDemoCommandTests(BaseTestCase):
    def _snapshot(self):
        return {
            "subjects": Subject.objects.count(),
            "offerings": SubjectOffering.objects.count(),
            "students": StudentProfile.objects.count(),
            "teachers": TeacherProfile.objects.count(),
            "enrollments": Enrollment.objects.count(),
        }

    def test_seed_creates_dataset_and_settings(self):
        call_command("seed_demo", verbosity=0)

        self.assertEqual(Subject.objects.count(), 4)
        self.assertEqual(SubjectOffering.objects.count(), 4)
        self.assertEqual(StudentProfile.objects.count(), 10)
        self.assertEqual(TeacherProfile.objects.count(), 3)
        self.assertEqual(Enrollment.objects.count(), 10 * 4)
        self.assertEqual(SystemSetting.get("attendance_threshold"), "60")

    def test_seed_is_idempotent(self):
        call_command("seed_demo", verbosity=0)
        first = self._snapshot()

        call_command("seed_demo", verbosity=0)
        second = self._snapshot()

        self.assertEqual(first, second)

    def test_seeded_student_profile_links_to_student_user(self):
        call_command("seed_demo", verbosity=0)

        profile = StudentProfile.objects.select_related("user").first()
        self.assertEqual(profile.user.role, "student")
        self.assertTrue(profile.user.check_password("demo12345"))

    def test_seed_creates_superuser_admin(self):
        from django.contrib.auth import get_user_model

        call_command("seed_demo", verbosity=0)

        admin = get_user_model().objects.get(username="admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, "admin")
        self.assertTrue(admin.check_password("demo12345"))
