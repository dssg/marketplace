from dssgmkt.models.user import UserNotification
from django.core.mail import send_mail

from decouple import config


class NotificationService():
    @staticmethod
    def add_user_notification(user, notification_description, severity, source, target_id):
        notification = UserNotification(user=user,
                                        notification_description=notification_description,
                                        severity=severity,
                                        source=source,
                                        target_id=target_id,
                                        is_read=False)
        notification.save()
        if user.email:
            message = "You have a new notification pending:\n{0}".format(notification_description)
            NotificationService.send_email(config('EMAIL_FROM_ADDRESS'), user.email, "[{0}] You have a new notification".format(config('SITE_NAME')), message)

    @staticmethod
    def add_multiuser_notification(users, notification_description, severity, source, target_id):
        for user in users:
            NotificationService.add_user_notification(user, notification_description, severity, source, target_id)

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
            send_mail(subject, message, from_email, to_email_or_list, fail_silently=False)
        except smtplib.SMTPException as e:
            # TODO log this exception
            print(str(e))
