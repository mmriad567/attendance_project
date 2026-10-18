from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import Role

from .base import BaseTestCase

User = get_user_model()


class UserModelTests(BaseTestCase):
    def test_auth_user_model_is_custom_user(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")

    def test_default_role_is_student(self):
        user = User.objects.create_user(username="s1", password="pw12345!")
        self.assertEqual(user.role, Role.STUDENT)
        self.assertTrue(user.is_student)

    def test_role_flags(self):
        admin = User.objects.create_user(username="a1", password="pw12345!", role=Role.ADMIN)
        teacher = User.objects.create_user(username="t1", password="pw12345!", role=Role.TEACHER)
        student = User.objects.create_user(username="s2", password="pw12345!", role=Role.STUDENT)

        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_teacher)
        self.assertTrue(teacher.is_teacher)
        self.assertFalse(teacher.is_student)
        self.assertTrue(student.is_student)

    def test_superuser_can_be_created(self):
        admin = User.objects.create_superuser(
            username="root", password="pw12345!", role=Role.ADMIN
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_admin)

    def test_role_choices(self):
        self.assertEqual(
            set(Role.values), {Role.ADMIN, Role.TEACHER, Role.STUDENT}
        )
