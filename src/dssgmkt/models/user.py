from django.contrib.auth.models import AbstractUser
from django.db import models

from dssgsolve import settings

from .common import PHONE_REGEX, ReviewStatus, OrgRole, SkillLevel

class UserType():
    DSSG_STAFF = 0
    VOLUNTEER = 1
    ORGANIZATION = 2
    def get_choices():
        return (
                (UserType.DSSG_STAFF, 'Site staff'),
                (UserType.VOLUNTEER, 'Volunteer'),
                (UserType.ORGANIZATION, 'Organization member'),
                )

class User(AbstractUser):
    initial_type = models.IntegerField(
        choices = UserType.get_choices(),
        default=UserType.VOLUNTEER,
    )
    skype_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    phone_number = models.CharField(
        validators=[PHONE_REGEX],
        max_length=17,
        blank=True,
        null=True,
    )
    special_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    def is_organization_member(self, orgid):
        return self.organizationrole_set.filter(organization=orgid).exists()

    def is_organization_staff(self, orgid):
        return self.organizationrole_set.filter(organization=orgid, role=OrgRole.STAFF).exists()

    def is_organization_admin(self, orgid):
        return self.organizationrole_set.filter(organization=orgid, role=OrgRole.ADMINISTRATOR).exists()


class NotificationSeverity():
    INFO = 0
    WARNING = 1
    ALERT = 2

    def get_choices():
        return (
                    (NotificationSeverity.INFO, 'Information'),
                    (NotificationSeverity.WARNING, 'Warning'),
                    (NotificationSeverity.ALERT, 'Alert'),
                )

class NotificationSource():
    GENERIC = 'GN'
    ORGANIZATION = 'OR'
    PROJECT = 'PJ'
    TASK = 'TK'
    VOLUNTEER_APPLICATION = 'VA'
    ORGANIZATION_MEMBERSHIP_REQUEST = 'OM'

    def get_choices():
        return (
                    (NotificationSource.GENERIC, 'Generic'),
                    (NotificationSource.ORGANIZATION, 'Organization'),
                    (NotificationSource.PROJECT, 'Project'),
                    (NotificationSource.TASK, 'Task'),
                    (NotificationSource.VOLUNTEER_APPLICATION, 'Volunteer application'),
                    (NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST, 'Organization membership request')
                )

class UserNotification(models.Model):
    notification_date = models.DateTimeField(auto_now_add=True)
    notification_description = models.CharField(max_length=500)
    is_read = models.BooleanField()

    severity = models.IntegerField(
        choices=NotificationSeverity.get_choices(),
        default=NotificationSeverity.INFO,
    )
    source = models.CharField(
        max_length=2,
        choices=NotificationSource.get_choices(),
        default=NotificationSource.GENERIC,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

class Skill(models.Model):
    area = models.CharField(max_length=50)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.area + "/" + self.name

    class Meta:
        unique_together = ('area','name')


class EducationLevel():
    BACHELORS = 0
    MASTERS = 1
    PHD = 2

    def get_choices():
        return (
                    (EducationLevel.BACHELORS, 'Bachelor\'s'),
                    (EducationLevel.MASTERS, 'Master\'s'),
                    (EducationLevel.PHD, 'PhD')
                )

class VolunteerProfile(models.Model):
    portfolio_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    github_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    linkedin_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    degree_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    degree_level = models.IntegerField(
        choices=EducationLevel.get_choices(),
        default=EducationLevel.BACHELORS,
    )
    university = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    cover_letter = models.TextField(
        max_length=2000,
        blank=True,
        null=True,
    )
    weekly_availability_hours = models.IntegerField()
    availability_start_date = models.DateField(
        blank=True,
        null=True,
    )
    availability_end_date = models.DateField(
        blank=True,
        null=True,
    )
    volunteer_status = models.CharField(
        max_length=3,
        choices=ReviewStatus.get_choices(),
        default=ReviewStatus.NEW,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )


class VolunteerSkill(models.Model):
    level = models.IntegerField(
        choices = SkillLevel.get_choices(),
        default=SkillLevel.BEGINNER,
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ('user','skill')
