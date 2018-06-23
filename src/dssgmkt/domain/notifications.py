from dssgmkt.models.user import UserNotification

class NotificationService():
    @staticmethod
    def add_user_notification(user, notification_description, severity, source):
        notification = UserNotification(user=user,
                                        notification_description=notification_description,
                                        severity=severity,
                                        source=source,
                                        is_read=False)
        notification.save()
