from django.conf import settings
from django.core.mail import send_mail

from .models import Notification, NotificationLevel


def notify(recipient, title, message="", level=NotificationLevel.INFO, link="", email=False):
    """Create an in-app notification and optionally send an email copy."""
    announcement = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        level=level,
        link=link,
    )
    if email and recipient.email:
        send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=True,
        )
    return announcement
