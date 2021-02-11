import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail

from namespaces import Namespace

from marketplace.models.user import UserNotification


LOG = logging.getLogger(__name__)


# Namespace declaration #

# TODO: continue/extend experiment with Namespaces over *Services


# Notification domain #

NotificationDomain = Namespace('notification')


@NotificationDomain
def add_user_notification(user, notification_description, severity, source, target_id):
    notification = UserNotification.objects.create(
        user=user,
        notification_description=notification_description,
        severity=severity,
        source=source,
        target_id=target_id,
        is_read=False,
    )

    if user.email:
        NotificationService.send_email(
            settings.DEFAULT_FROM_EMAIL,
            user.email,
            f"[{settings.SITE_NAME}] You have a new notification",
            f"You have a new notification pending:\n\n{notification_description}",
        )


class NotificationService:

    @staticmethod
    def add_multiuser_notification(users, notification_description, severity, source, target_id):
        for user in users:
            add_user_notification(user, notification_description, severity, source, target_id)

    @staticmethod
    def mark_notifications_as_read(user_notification_list):
        for notification in user_notification_list:
            notification.is_read = True
            notification.save()

    @staticmethod
    def send_email(from_email, to_email_or_list, subject, message):
        if isinstance(to_email_or_list, str):
            to_email_or_list = [to_email_or_list]

        try:
            send_mail(
                subject,
                message,
                from_email,
                to_email_or_list,
                fail_silently=False,
            )
        except (OSError, SMTPException):
            LOG.exception("send_mail failed [from_email: %r] [to_email: %r]",
                          from_email, to_email_or_list)
