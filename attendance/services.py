from django.conf import settings
from django.db import transaction

from academics.models import Enrollment, SubjectOffering

from .models import AttendanceRecord, AttendanceStatus, ClassSession

# A student is considered to have attended a class when marked present or late.
ATTENDED_STATUSES = (AttendanceStatus.PRESENT, AttendanceStatus.LATE)


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


def _percentage(attended, total):
    if not total:
        return None
    return round(attended / total * 100, 1)


def offering_stats(student, offering, threshold=None):
    """Attendance breakdown for one student in one offering."""
    if threshold is None:
        threshold = getattr(settings, "ATTENDANCE_THRESHOLD", 60)

    records = AttendanceRecord.objects.filter(
        student=student, class_session__offering=offering
    )
    total = records.count()
    counts = {
        status.value: records.filter(status=status.value).count()
        for status in AttendanceStatus
    }
    attended = sum(counts[status.value] for status in ATTENDED_STATUSES)
    percentage = _percentage(attended, total)

    return {
        "offering": offering,
        "total": total,
        "attended": attended,
        "percentage": percentage,
        "below_threshold": percentage is not None and percentage < threshold,
        **counts,
    }


def student_summary(student, threshold=None):
    """Overall and per-offering attendance for a student across active enrollments."""
    if threshold is None:
        threshold = getattr(settings, "ATTENDANCE_THRESHOLD", 60)

    offerings = (
        SubjectOffering.objects.filter(
            enrollments__student=student, enrollments__is_active=True
        )
        .select_related("subject", "session")
        .distinct()
        .order_by("subject__code")
    )

    rows = [offering_stats(student, offering, threshold) for offering in offerings]
    total = sum(row["total"] for row in rows)
    attended = sum(row["attended"] for row in rows)
    percentage = _percentage(attended, total)

    return {
        "student": student,
        "rows": rows,
        "total": total,
        "attended": attended,
        "percentage": percentage,
        "threshold": threshold,
        "below_threshold": percentage is not None and percentage < threshold,
        "low_offerings": [row for row in rows if row["below_threshold"]],
    }


def offering_student_rows(offering, threshold=None):
    """Per-student attendance breakdown for one offering."""
    if threshold is None:
        threshold = getattr(settings, "ATTENDANCE_THRESHOLD", 60)

    enrollments = (
        offering.enrollments.filter(is_active=True)
        .select_related("student__user")
        .order_by("student__roll_no")
    )

    rows = []
    for enrollment in enrollments:
        stats = offering_stats(enrollment.student, offering, threshold)
        rows.append(
            {
                "student": enrollment.student,
                "total": stats["total"],
                "present": stats["present"],
                "late": stats["late"],
                "absent": stats["absent"],
                "excused": stats["excused"],
                "attended": stats["attended"],
                "percentage": stats["percentage"],
                "below_threshold": stats["below_threshold"],
            }
        )
    return rows


def offering_status_distribution(offering):
    """Total count of each status across all sessions of an offering."""
    records = AttendanceRecord.objects.filter(class_session__offering=offering)
    return {
        status.value: records.filter(status=status.value).count()
        for status in AttendanceStatus
    }


def offering_trends(offering):
    """Attendance percentage for each session (oldest first), for charts."""
    sessions = (
        ClassSession.objects.filter(offering=offering)
        .order_by("date", "period_no")
        .prefetch_related("records")
    )
    trends = []
    for session in sessions:
        total = session.records.count()
        if not total:
            continue
        attended = session.records.filter(
            status__in=[s.value for s in ATTENDED_STATUSES]
        ).count()
        trends.append(
            {
                "label": f"{session.date:%d %b} P{session.period_no}",
                "percentage": round(attended / total * 100, 1),
            }
        )
    return trends
