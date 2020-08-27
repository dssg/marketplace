from django.core import mail
from django.test import TestCase

from marketplace.domain import marketplace
from marketplace.models.user import (
    NotificationSeverity,
    NotificationSource,
    UserNotification,
)

from . import common


class NotificationsTestCase(TestCase):

    def test_add_user_notification(self):
        "can add user notification of arbitrary length"
        self.assertEqual(UserNotification.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        volunteer = common.example_volunteer_user()
        marketplace.user.add_user(volunteer, 'volunteer')

        marketplace.notification.add_user_notification(
            volunteer,
            """
            Congratulations! you have been accepted as a volunteer and can now apply to work on
            open projects.

            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
            incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
            exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure
            dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
            Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt
            mollit anim id est laborum.
            """,
            NotificationSeverity.INFO,
            NotificationSource.VOLUNTEER_APPLICATION,
            volunteer.volunteerprofile.id,
        )

        self.assertEqual(UserNotification.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        # the method under test is perhaps too low-level for it to make sense for it to run model
        # validations. rather, this is done here to ensure that the notification (was) proper,
        # regardless of database backend -- **sqlite3 does not enforce length**.
        notification = UserNotification.objects.get()
        notification.full_clean()

        (email,) = mail.outbox
        self.assertEqual(email.to, [volunteer.email])
