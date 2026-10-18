from django.db import transaction

from academics.models import Enrollment

from .models import AttendanceRecord, ClassSession


@transaction.atomic
def create_class_session(
    *, offering, date, period_no, created_by, start_time=None, end_time=None, topic=""
):
    """Create a session and pre-create one ABSENT record per enrolled student."""
    session = ClassSession.objects.create(
        offering=offering,
        date=date,
        period_no=period_no,
        start_time=start_time,
        end_time=end_time,
        topic=topic,
        created_by=created_by,
    )

    student_ids = (
        Enrollment.objects.filter(offering=offering, is_active=True)
        .values_list("student_id", flat=True)
    )
    AttendanceRecord.objects.bulk_create(
        [AttendanceRecord(class_session=session, student_id=sid) for sid in student_ids]
    )
    return session
