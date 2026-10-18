from django.conf import settings


def site_settings(request):
    return {
        "INSTITUTE_NAME": settings.INSTITUTE_NAME,
        "ATTENDANCE_THRESHOLD": settings.ATTENDANCE_THRESHOLD,
    }
