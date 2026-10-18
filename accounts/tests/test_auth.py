from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Role

from .base import BaseTestCase

User = get_user_model()


class LoginViewTests(BaseTestCase):
    def setUp(self):
        self.url = reverse("accounts:login")
        self.user = User.objects.create_user(
            username="alice", password="secret-pass-123", role=Role.STUDENT
        )

    def test_login_page_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_login_success_redirects_home(self):
        response = self.client.post(
            self.url, {"username": "alice", "password": "secret-pass-123"}
        )
        self.assertRedirects(response, reverse("accounts:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_wrong_password_fails(self):
        response = self.client.post(
            self.url, {"username": "alice", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_authenticated_user_is_redirected_away_from_login(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("accounts:home"))


class LogoutViewTests(BaseTestCase):
    def test_logout_redirects_to_login(self):
        user = User.objects.create_user(username="bob", password="pw12345!")
        self.client.force_login(user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class HomeViewTests(BaseTestCase):
    def test_home_requires_login(self):
        response = self.client.get(reverse("accounts:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_home_renders_for_authenticated_user(self):
        user = User.objects.create_user(username="carol", password="pw12345!")
        self.client.force_login(user)
        response = self.client.get(reverse("accounts:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/dashboard.html")
        self.assertContains(response, "carol")

    def test_teacher_is_redirected_to_attendance_dashboard(self):
        teacher = User.objects.create_user(
            username="teach", password="pw12345!", role=Role.TEACHER
        )
        self.client.force_login(teacher)
        response = self.client.get(reverse("accounts:home"))
        self.assertRedirects(response, reverse("attendance:dashboard"))
