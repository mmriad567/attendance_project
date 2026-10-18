from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from accounts.models import StudentProfile, StudentStatus
from attendance.services import student_summary
from notifications.models import NotificationLevel
from notifications.services import notify


class Command(BaseCommand):
    help = "Notify students whose overall attendance is below the threshold."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-email",
            action="store_true",
            help="Only create in-app notifications, do not send email.",
        )

    def handle(self, *args, **options):
        threshold = getattr(settings, "ATTENDANCE_THRESHOLD", 60)
        created = 0

        students = StudentProfile.objects.filter(
            status=StudentStatus.ACTIVE
        ).select_related("user")

        for student in students:
            summary = student_summary(student, threshold)
            if summary["percentage"] is None or not summary["below_threshold"]:
                continue

            title = "Low attendance warning"
            if student.user.notifications.filter(title=title, is_read=False).exists():
                continue

            message = (
                f"Your overall attendance is {summary['percentage']}%, "
                f"below the required {threshold}%. Please attend classes regularly."
            )
            notify(
                student.user,
                title,
                message,
                level=NotificationLevel.WARNING,
                link=reverse("students:dashboard"),
                email=not options["no_email"],
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} low-attendance notification(s).")
        )
