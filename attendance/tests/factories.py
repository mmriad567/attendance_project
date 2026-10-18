from django.contrib.auth import get_user_model

from academics.models import Enrollment, Subject, SubjectOffering, SubjectType
from accounts.models import (
    AcademicSession,
    Department,
    Role,
    Shift,
    StudentProfile,
    TeacherProfile,
)

User = get_user_model()


class OfferingFixture:
    def __init__(self, offering, teacher, students):
        self.offering = offering
        self.teacher = teacher
        self.students = students


def build_offering(*, num_students=3, code="28531", teacher=None):
    """Create a full offering with a teacher and enrolled students."""
    department = Department.objects.create(code=f"D{code}", name=f"Dept {code}")
    session = AcademicSession.objects.create(name=f"S{code}")

    if teacher is None:
        teacher = User.objects.create_user(
            username=f"teacher.{code}", password="pw12345!", role=Role.TEACHER
        )
        TeacherProfile.objects.create(
            user=teacher, employee_id=f"EMP-{code}", department=department
        )

    subject = Subject.objects.create(
        code=code,
        name=f"Subject {code}",
        department=department,
        semester=3,
        subject_type=SubjectType.THEORY,
        credit=3.0,
    )
    offering = SubjectOffering.objects.create(
        subject=subject,
        session=session,
        semester=3,
        shift=Shift.FIRST,
        section="A",
        teacher=teacher,
    )

    students = []
    for index in range(1, num_students + 1):
        user = User.objects.create_user(
            username=f"stu.{code}.{index}", password="pw12345!", role=Role.STUDENT
        )
        profile = StudentProfile.objects.create(
            user=user,
            roll_no=f"{code}{index:03d}",
            department=department,
            session=session,
            section="A",
        )
        Enrollment.objects.create(student=profile, offering=offering)
        students.append(profile)

    return OfferingFixture(offering, teacher, students)
