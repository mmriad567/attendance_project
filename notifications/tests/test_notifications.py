from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.tests.base import BaseTestCase
from attendance.models import AttendanceStatus
from attendance.services import create_class_session
from attendance.tests.factories import build_offering
from notifications.models import Notification

User = get_user_model()


class NotificationModelTests(BaseTestCase):
    def test_mark_read_sets_flag_and_timestamp(self):
        user = User.objects.create_user(username="u1", password="pw12345!")
        note = Notification.objects.create(recipient=user, title="Hi")
        note.mark_read()
        note.refresh_from_db()
        self.assertTrue(note.is_read)
        self.assertIsNotNone(note.read_at)


class NotificationViewTests(BaseTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pw12345!")
        self.other = User.objects.create_user(username="u2", password="pw12345!")
        Notification.objects.create(recipient=self.user, title="Mine")
        Notification.objects.create(recipient=self.other, title="Theirs")

    def test_list_requires_login(self):
        response = self.client.get(reverse("notifications:list"))
        self.assertEqual(response.status_code, 302)

    def test_list_shows_only_own(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("notifications:list"))
        self.assertContains(response, "Mine")
        self.assertNotContains(response, "Theirs")

    def test_mark_read(self):
        self.client.force_login(self.user)
        note = self.user.notifications.first()
        response = self.client.post(reverse("notifications:mark_read", args=[note.pk]))
        self.assertEqual(response.status_code, 204)
        note.refresh_from_db()
        self.assertTrue(note.is_read)

    def test_mark_all_read(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("notifications:mark_all_read"))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.user.notifications.filter(is_read=False).count(), 0)


class CheckAttendanceCommandTests(BaseTestCase):
    def setUp(self):
        self.fx = build_offering(num_students=2, code="28531")
        self.good, self.bad = self.fx.students
        for student in self.fx.students:
            student.user.email = f"{student.user.username}@example.com"
            student.user.save(update_fields=["email"])

        for period in range(1, 4):
            session = create_class_session(
                offering=self.fx.offering,
                date=timezone.localdate(),
                period_no=period,
                created_by=self.fx.teacher,
            )
            session.records.filter(student=self.good).update(
                status=AttendanceStatus.PRESENT
            )
            session.records.filter(student=self.bad).update(
                status=AttendanceStatus.ABSENT
            )

    def test_creates_warning_for_low_attendance_only(self):
        call_command("check_attendance", "--no-email", verbosity=0)
        self.assertEqual(self.bad.user.notifications.count(), 1)
        self.assertEqual(self.good.user.notifications.count(), 0)

    def test_sends_email_when_not_disabled(self):
        call_command("check_attendance", verbosity=0)
        self.assertEqual(len(mail.outbox), 1)

    def test_does_not_duplicate_unread_warnings(self):
        call_command("check_attendance", "--no-email", verbosity=0)
        call_command("check_attendance", "--no-email", verbosity=0)
        self.assertEqual(self.bad.user.notifications.count(), 1)
