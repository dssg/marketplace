from dssgmkt.models.user import UserNotification

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

    @staticmethod
    def add_multiuser_notification(users, notification_description, severity, source, target_id):
        for user in users:
            NotificationService.add_user_notification(user, notification_description, severity, source, target_id)

    @staticmethod
    def mark_notifications_as_read(user_notification_list):
        for notification in user_notification_list:
            notification.is_read = True
            notification.save()
