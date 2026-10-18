"""Populate the database with a small, idempotent demo dataset.

Safe to run repeatedly: every object is created with ``get_or_create`` keyed on
a stable identifier, so re-running only reports existing counts.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from academics.models import Enrollment, Subject, SubjectOffering, SubjectType
from accounts.models import (
    AcademicSession,
    Department,
    Designation,
    Role,
    Shift,
    StudentProfile,
    TeacherProfile,
)
from core.models import SystemSetting

User = get_user_model()

DEMO_PASSWORD = "demo12345"

DEPARTMENTS = [
    {"code": "CST", "name": "Computer Science and Technology", "short_name": "CST"},
    {"code": "EEE", "name": "Electrical and Electronics Engineering", "short_name": "EEE"},
    {"code": "MEC", "name": "Mechanical Engineering", "short_name": "MEC"},
]

TEACHERS = [
    {"username": "teacher.rahim", "first": "Rahim", "last": "Uddin", "emp": "EMP-001", "designation": Designation.CHIEF_INSTRUCTOR},
    {"username": "teacher.karim", "first": "Karim", "last": "Ahmed", "emp": "EMP-002", "designation": Designation.INSTRUCTOR},
    {"username": "teacher.sultana", "first": "Sultana", "last": "Begum", "emp": "EMP-003", "designation": Designation.JUNIOR_INSTRUCTOR},
]

CST_SEM3_SUBJECTS = [
    {"code": "28531", "name": "Object Oriented Programming", "type": SubjectType.THEORY, "credit": 3.0},
    {"code": "28532", "name": "Object Oriented Programming Lab", "type": SubjectType.PRACTICAL, "credit": 2.0},
    {"code": "28511", "name": "Data Communication", "type": SubjectType.THEORY, "credit": 3.0},
    {"code": "28521", "name": "Web Technology", "type": SubjectType.THEORY, "credit": 3.0},
]

STUDENT_NAMES = [
    ("Ayesha", "Akter"),
    ("Mehedi", "Hasan"),
    ("Nusrat", "Jahan"),
    ("Rakib", "Hossain"),
    ("Sadia", "Islam"),
    ("Tanvir", "Alam"),
    ("Fatema", "Khatun"),
    ("Imran", "Kabir"),
    ("Jannat", "Ferdous"),
    ("Shakib", "Ahmed"),
]


class Command(BaseCommand):
    help = "Create demo departments, sessions, teachers, students, subjects and enrollments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--semester",
            type=int,
            default=3,
            help="Semester used when building the demo offerings (default: 3).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        semester = options["semester"]

        for key, value, desc in [
            ("institute_name", "Polytechnic Institute", "Name shown in the header"),
            ("attendance_threshold", "60", "Minimum passing attendance percentage"),
        ]:
            SystemSetting.set(key, value, desc)

        departments = {}
        for data in DEPARTMENTS:
            dept, _ = Department.objects.get_or_create(
                code=data["code"],
                defaults={"name": data["name"], "short_name": data["short_name"]},
            )
            departments[data["code"]] = dept

        session, _ = AcademicSession.objects.get_or_create(
            name="2022-2023",
            defaults={"start_date": date(2022, 8, 1), "is_current": True},
        )
        AcademicSession.objects.get_or_create(
            name="2023-2024", defaults={"start_date": date(2023, 8, 1)}
        )

        cst = departments["CST"]

        teachers = []
        for data in TEACHERS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "role": Role.TEACHER,
                    "first_name": data["first"],
                    "last_name": data["last"],
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            profile, _ = TeacherProfile.objects.get_or_create(
                user=user,
                defaults={
                    "employee_id": data["emp"],
                    "department": cst,
                    "designation": data["designation"],
                },
            )
            teachers.append(profile)

        subjects = []
        for data in CST_SEM3_SUBJECTS:
            subject, _ = Subject.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "department": cst,
                    "semester": semester,
                    "subject_type": data["type"],
                    "credit": data["credit"],
                    "weekly_classes": 1,
                },
            )
            subjects.append(subject)

        offerings = []
        for index, subject in enumerate(subjects):
            offering, _ = SubjectOffering.objects.get_or_create(
                subject=subject,
                session=session,
                semester=semester,
                shift=Shift.FIRST,
                section="A",
                defaults={"teacher": teachers[index % len(teachers)].user},
            )
            offerings.append(offering)

        students = []
        for index, (first, last) in enumerate(STUDENT_NAMES, start=1):
            roll = f"2022{index:03d}"
            user, created = User.objects.get_or_create(
                username=f"student.{roll}",
                defaults={
                    "role": Role.STUDENT,
                    "first_name": first,
                    "last_name": last,
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "roll_no": roll,
                    "registration_no": f"150{2022000 + index}",
                    "department": cst,
                    "session": session,
                    "shift": Shift.FIRST,
                    "section": "A",
                    "current_semester": semester,
                    "guardian_name": f"{last} Guardian",
                    "guardian_phone": "0170000000",
                },
            )
            students.append(profile)

        enrollment_count = 0
        for student in students:
            for offering in offerings:
                _, created = Enrollment.objects.get_or_create(
                    student=student, offering=offering
                )
                enrollment_count += int(created)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(
            f"  departments: {Department.objects.count()}  "
            f"sessions: {AcademicSession.objects.count()}  "
            f"subjects: {Subject.objects.count()}  "
            f"offerings: {SubjectOffering.objects.count()}"
        )
        self.stdout.write(
            f"  teachers: {TeacherProfile.objects.count()}  "
            f"students: {StudentProfile.objects.count()}  "
            f"enrollments created now: {enrollment_count}"
        )
        self.stdout.write(f"  demo login password for seeded users: {DEMO_PASSWORD}")
