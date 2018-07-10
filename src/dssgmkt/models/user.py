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
        verbose_name="Initial type of user",
        help_text="Users can check their preference when they sign up to indicate they want to be volunteers or create/join organizations",
        choices = UserType.get_choices(),
        default=UserType.VOLUNTEER,
    )
    skype_name = models.CharField(
        verbose_name="Skype user name",
        max_length=50,
        blank=True,
        null=True,
    )
    phone_number = models.CharField(
        verbose_name="Phone number",
        help_text="Type your phone number in the format +999999999999999",
        validators=[PHONE_REGEX],
        max_length=17,
        blank=True,
        null=True,
    )
    special_code = models.CharField(
        verbose_name="Special signup code",
        help_text="Do you have a signup code from the person or organization that referred you to this site? These codes may unlock special features, so do not forget to use one if you have it.",
        max_length=20,
        blank=True,
        null=True,
    )

    def full_name(self):
        return self.first_name + " " + self.last_name

    def standard_display_name(self):
        return self.full_name() + "(" + self.username + ")"

class NotificationSeverity():
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3

    def get_choices():
        return (
                    (NotificationSeverity.INFO, 'Information'),
                    (NotificationSeverity.WARNING, 'Warning'),
                    (NotificationSeverity.ERROR, 'Error'),
                    (NotificationSeverity.CRITICAL, 'Critical'),
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
    target_id = models.IntegerField(
        verbose_name="Target ID",
        help_text="ID of the target entity that is related to this notification",
        blank=True,
        null=True,
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

    def standard_display_name(self):
        return str(self)

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
        verbose_name="Portfolio URL",
        help_text="Include any external site that has a showcase of your experience, skills, and/or background, and that projects may consider interesting or relevant to them",
        max_length=200,
        blank=True,
        null=True,
    )
    github_url = models.URLField(
        verbose_name="Github URL",
        help_text="Add a link to your Github profile if you want to share code with potential projects so they can review your skills.",
        max_length=200,
        blank=True,
        null=True,
    )
    linkedin_url = models.URLField(
        verbose_name="LinkedIn URL",
        help_text="Add a link to your LinkedIn profile to show potential projects your professional background and experience.",
        max_length=200,
        blank=True,
        null=True,
    )
    degree_name = models.CharField(
        verbose_name="Degree name",
        help_text="The name of the highest level degree you have. For example, Computer Science or Economics.",
        max_length=50,
        blank=True,
        null=True,
    )
    degree_level = models.IntegerField(
        verbose_name="Degree level",
        help_text="The level of the highest level degree you have.",
        choices=EducationLevel.get_choices(),
        default=EducationLevel.BACHELORS,
        blank=True,
        null=True,
    )
    university = models.CharField(
        verbose_name="Educational institution",
        help_text="The name of the institution (university, school, etc.) that issued the highest level degree you have.",
        max_length=50,
        blank=True,
        null=True,
    )
    cover_letter = models.TextField(
        verbose_name="Cover letter",
        help_text="Introduce yourself and tell projects and volunteers about your background and skills, your motivation for volunteering, your preferences for projects and work, what you want to acoomplish, and any other thing that you can think of.",
        max_length=2000,
        blank=True,
        null=True,
    )
    weekly_availability_hours = models.PositiveSmallIntegerField(
        verbose_name="Weekly availability (hours)",
        help_text="Roughly, how many hours can you dedicate each week to volunteer work?",
        blank=True,
        null=True,
    )
    availability_start_date = models.DateField(
        verbose_name="Availability start date",
        help_text="When are you available to start working on projects? Leave this field blank if you can start at any time.",
        blank=True,
        null=True,
    )
    availability_end_date = models.DateField(
        verbose_name="Availability end date",
        help_text="When is the latest date you are available for working on projects? Leave this field blank if you don't have restrictions on your availability.",
        blank=True,
        null=True,
    )
    volunteer_status = models.CharField(
        verbose_name="Volunteer status",
        help_text="Describes if volunteers have been approved to apply to projects or if they still are pending approval.",
        max_length=3,
        choices=ReviewStatus.get_choices(),
        default=ReviewStatus.NEW,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="User",
        help_text="User this volunteer profile is attached to.",
    )


class VolunteerSkill(models.Model):
    level = models.IntegerField(
        verbose_name="Skill level",
        help_text="How proficient are you in this skill?",
        choices = SkillLevel.get_choices(),
        default=SkillLevel.BEGINNER,
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        verbose_name="Skill",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="User",
    )

    class Meta:
        unique_together = ('user','skill')
