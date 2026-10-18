from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    ABSENT = "absent", "Absent"
    LATE = "late", "Late"
    EXCUSED = "excused", "Excused"


def edit_window_days():
    return getattr(settings, "ATTENDANCE_EDIT_WINDOW_DAYS", 3)


class ClassSession(models.Model):
    """A single class period for a subject offering on a given date."""

    offering = models.ForeignKey(
        "academics.SubjectOffering",
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    date = models.DateField()
    period_no = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    topic = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="created_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-date", "period_no")
        constraints = [
            models.UniqueConstraint(
                fields=["offering", "date", "period_no"],
                name="unique_session_per_offering_date_period",
            )
        ]
        indexes = [models.Index(fields=["date"])]

    def __str__(self):
        return f"{self.offering.subject.code} · {self.date} · P{self.period_no}"

    @property
    def is_editable(self):
        window = edit_window_days()
        return self.date >= timezone.localdate() - timedelta(days=window)

    @property
    def present_count(self):
        return self.records.filter(status=AttendanceStatus.PRESENT).count()

    @property
    def total_count(self):
        return self.records.count()


class AttendanceRecord(models.Model):
    class_session = models.ForeignKey(
        ClassSession, on_delete=models.CASCADE, related_name="records"
    )
    student = models.ForeignKey(
        "accounts.StudentProfile",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    status = models.CharField(
        max_length=10,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ABSENT,
    )
    remark = models.CharField(max_length=200, blank=True)
    marked_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="marked_records",
        blank=True,
        null=True,
    )
    marked_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("student__roll_no",)
        constraints = [
            models.UniqueConstraint(
                fields=["class_session", "student"],
                name="unique_record_per_session_student",
            )
        ]
        indexes = [models.Index(fields=["student", "status"])]

    def __str__(self):
        return f"{self.student.roll_no} · {self.class_session} · {self.get_status_display()}"

    def mark(self, status, by):
        self.status = status
        self.marked_by = by
        self.marked_at = timezone.now()
        self.save(update_fields=["status", "marked_by", "marked_at", "updated_at"])
