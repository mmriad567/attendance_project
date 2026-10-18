from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    TEACHER = "teacher", "Teacher"
    STUDENT = "student", "Student"


class Shift(models.TextChoices):
    FIRST = "1st", "First"
    SECOND = "2nd", "Second"


class StudentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    GRADUATED = "graduated", "Graduated"
    DROPPED = "dropped", "Dropped"


class Designation(models.TextChoices):
    CHIEF_INSTRUCTOR = "chief_instructor", "Chief Instructor"
    INSTRUCTOR = "instructor", "Instructor"
    JUNIOR_INSTRUCTOR = "junior_instructor", "Junior Instructor"
    LAB_INSTRUCTOR = "lab_instructor", "Lab Instructor"


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_student(self):
        return self.role == Role.STUDENT


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    short_name = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return f"{self.code} - {self.name}"


class AcademicSession(models.Model):
    """An admission batch, e.g. "2022-2023"."""

    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ("-name",)

    def __str__(self):
        return self.name


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": Role.STUDENT},
    )
    roll_no = models.CharField(max_length=20)
    registration_no = models.CharField(max_length=30, unique=True, blank=True, null=True)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="students"
    )
    session = models.ForeignKey(
        AcademicSession, on_delete=models.PROTECT, related_name="students"
    )
    shift = models.CharField(max_length=5, choices=Shift.choices, default=Shift.FIRST)
    section = models.CharField(max_length=10, blank=True)
    current_semester = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(8)],
    )
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    admission_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=StudentStatus.choices, default=StudentStatus.ACTIVE
    )

    class Meta:
        ordering = ("department", "session", "roll_no")
        constraints = [
            models.UniqueConstraint(
                fields=["roll_no", "session", "department"],
                name="unique_roll_per_session_department",
            )
        ]

    def __str__(self):
        return f"{self.roll_no} - {self.user.get_full_name() or self.user.username}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": Role.TEACHER},
    )
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="teachers"
    )
    designation = models.CharField(
        max_length=30,
        choices=Designation.choices,
        default=Designation.INSTRUCTOR,
    )

    class Meta:
        ordering = ("employee_id",)

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"
