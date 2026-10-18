from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from accounts.models import Role

from .base import BaseTestCase

User = get_user_model()

TEST_URLCONF = "accounts.tests.urls"


@override_settings(ROOT_URLCONF=TEST_URLCONF)
class RoleRequiredMixinTests(BaseTestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="a", password="pw12345!", role=Role.ADMIN)
        self.teacher = User.objects.create_user(username="t", password="pw12345!", role=Role.TEACHER)
        self.student = User.objects.create_user(username="s", password="pw12345!", role=Role.STUDENT)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("admin_only"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_allowed_role_gets_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_only"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"admin-ok")

    def test_disallowed_role_is_forbidden(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("admin_only"))
        self.assertEqual(response.status_code, 403)

    def test_student_forbidden_on_admin_view(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("admin_only"))
        self.assertEqual(response.status_code, 403)

    def test_multiple_allowed_roles(self):
        for user in (self.admin, self.teacher):
            self.client.force_login(user)
            response = self.client.get(reverse("teacher_only"))
            self.assertEqual(response.status_code, 200)

    def test_empty_allowed_roles_permits_any_authenticated_user(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("any_role"))
        self.assertEqual(response.status_code, 200)
