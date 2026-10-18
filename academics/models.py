from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from accounts.models import Role, Shift

SEMESTER_VALIDATORS = [MinValueValidator(1), MaxValueValidator(8)]


class SubjectType(models.TextChoices):
    THEORY = "theory", "Theory"
    PRACTICAL = "practical", "Practical"


class Subject(models.Model):
    """A catalog subject as defined by BTEB, e.g. code 25611."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    department = models.ForeignKey(
        "accounts.Department", on_delete=models.PROTECT, related_name="subjects"
    )
    semester = models.PositiveSmallIntegerField(validators=SEMESTER_VALIDATORS)
    subject_type = models.CharField(
        max_length=10, choices=SubjectType.choices, default=SubjectType.THEORY
    )
    credit = models.DecimalField(max_digits=3, decimal_places=1, default=3.0)
    weekly_classes = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return f"{self.code} - {self.name}"


class SubjectOffering(models.Model):
    """A subject as taught to a specific batch/shift/section in a session."""

    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name="offerings"
    )
    session = models.ForeignKey(
        "accounts.AcademicSession", on_delete=models.PROTECT, related_name="offerings"
    )
    semester = models.PositiveSmallIntegerField(validators=SEMESTER_VALIDATORS)
    shift = models.CharField(max_length=5, choices=Shift.choices, default=Shift.FIRST)
    section = models.CharField(max_length=10, blank=True)
    teacher = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="offerings",
        limit_choices_to={"role": Role.TEACHER},
    )
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ("session", "semester", "subject")
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "session", "semester", "shift", "section"],
                name="unique_offering_per_subject_batch",
            )
        ]

    def __str__(self):
        return f"{self.subject.code} ({self.session}, Sem {self.semester})"


class Enrollment(models.Model):
    student = models.ForeignKey(
        "accounts.StudentProfile", on_delete=models.CASCADE, related_name="enrollments"
    )
    offering = models.ForeignKey(
        SubjectOffering, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("student", "offering")
        constraints = [
            models.UniqueConstraint(
                fields=["student", "offering"], name="unique_student_offering"
            )
        ]

    def __str__(self):
        return f"{self.student.roll_no} → {self.offering.subject.code}"
