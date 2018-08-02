from django.conf import settings
from django.contrib.auth.models import (
    AbstractUser,
    UserManager as AuthUserManager,
)
from django.db import models

from .common import (
    ReviewStatus,
    OrgRole,
    SkillLevel,
    validate_image_size,
)


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


class UserManager(AuthUserManager):

    def create_superuser(self, *args, **kwargs):
        kwargs.setdefault('initial_type', UserType.DSSG_STAFF)
        return super().create_superuser(*args, **kwargs)


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
        # validators=[PHONE_REGEX],
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
    profile_image_file = models.ImageField(
        verbose_name="Profile image",
        help_text="Your profile image.",
        upload_to="userprofiles/",
        blank=True,
        null=True,
        validators=[validate_image_size],
    )

    objects = UserManager()

    def full_name(self):
        return self.first_name + " " + self.last_name

    def standard_display_name(self):
        return self.full_name() + "(" + self.username + ")"

    def is_type_dssg_staff(self):
        return self.initial_type == UserType.DSSG_STAFF

class SignupCodeType():
    VOLUNTEER_AUTOMATIC_ACCEPT = 0
    MAKE_DSSG_STAFF = 1

    def get_choices():
        return (
                    (SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT, 'Automatically accept user as volunteer'),
                    (SignupCodeType.MAKE_DSSG_STAFF, 'Automatically make users DSSG staff members so they can review volunteer applications'),
                )

class SignupCode(models.Model):
    name = models.CharField(
        verbose_name="Signup code",
        help_text="A code that users can type when signing up in the site that will grant them benefits.",
        max_length=50,
    )
    type = models.IntegerField(
        choices=SignupCodeType.get_choices(),
        default=SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT,
    )
    expiration_date = models.DateField(
        verbose_name="Expiration date",
        help_text="Expiration date after which the code will no longer valid",
        blank=True,
        null=True,
    )
    max_uses = models.IntegerField(
        verbose_name="Maximum number of uses",
        help_text="Maximum number of users that can use this code, if any.",
        blank=True,
        null=True,
    )
    current_uses = models.IntegerField(
        verbose_name="Times used",
        help_text="Number of times this code has been used.",
        default=0,
        blank=True,
        null=True,
    )


class NotificationSeverity():
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3

    def get_choices():
        return (
                    (NotificationSeverity.INFO, 'info'),
                    (NotificationSeverity.WARNING, 'warning'),
                    (NotificationSeverity.ERROR, 'danger'),
                    (NotificationSeverity.CRITICAL, 'primary'),
                )

class NotificationSource():
    GENERIC = 'GN'
    ORGANIZATION = 'OR'
    PROJECT = 'PJ'
    TASK = 'TK'
    VOLUNTEER_APPLICATION = 'VA'
    ORGANIZATION_MEMBERSHIP_REQUEST = 'OM'
    BADGE = 'BA'

    def get_choices():
        return (
                    (NotificationSource.GENERIC, 'Generic'),
                    (NotificationSource.ORGANIZATION, 'Organization'),
                    (NotificationSource.PROJECT, 'Project'),
                    (NotificationSource.TASK, 'Task'),
                    (NotificationSource.VOLUNTEER_APPLICATION, 'Volunteer application'),
                    (NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST, 'Organization membership request'),
                    (NotificationSource.BADGE, 'Award'),
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

    def is_source_organization(self):
        return self.source == NotificationSource.ORGANIZATION

    def is_source_project(self):
        return self.source == NotificationSource.PROJECT

    def is_source_task(self):
        return self.source == NotificationSource.TASK

    def is_source_volunteer_application(self):
        return self.source == NotificationSource.VOLUNTEER_APPLICATION

    def is_source_organization_membership_request(self):
        return self.source == NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST

    def is_source_badge(self):
        return self.source == NotificationSource.BADGE

class Skill(models.Model):
    area = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.area + "/" + self.name

    def standard_display_name(self):
        return str(self)

    class Meta:
        unique_together = ('area','name')


class EducationLevel():
    OTHER = 0
    PRIMARY = 1
    SECONDARY = 2
    BACHELORS = 3
    MASTERS = 4
    PHD = 5

    def get_choices():
        return (
                    (EducationLevel.OTHER, 'Other'),
                    (EducationLevel.PRIMARY, 'Primary education'),
                    (EducationLevel.SECONDARY, 'Secondary education'),
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
    completed_task_count = models.PositiveSmallIntegerField(
        verbose_name="Completed task count",
        help_text="Number of task this user has completed",
        blank=True,
        null=True,
    )
    average_review_score = models.FloatField(
        verbose_name="Average review score",
        help_text="Average review score",
        blank=True,
        null=True,
    )
    ahead_of_time_task_ratio = models.FloatField(
        verbose_name="Ratio of tasks ahead of time",
        help_text="Ratio of the tasks that the user completed ahead of the estimated time.",
        blank=True,
        null=True,
    )
    is_edited = models.BooleanField(
        verbose_name="Is edited?",
        help_text="Specifies if the user has edited the profile or if it has the default initial settings.",
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="User",
        help_text="User this volunteer profile is attached to.",
    )

    def is_pending_review(self):
        return self.volunteer_status == ReviewStatus.NEW

    def is_accepted(self):
        return self.volunteer_status == ReviewStatus.ACCEPTED

    def is_rejected(self):
        return self.volunteer_status == ReviewStatus.REJECTED


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

    def is_level_beginner(self):
        return self.level == SkillLevel.BEGINNER

    def is_level_intermediate(self):
        return self.level == SkillLevel.INTERMEDIATE

    def is_level_expert(self):
        return self.level == SkillLevel.EXPERT

    class Meta:
        unique_together = ('user','skill')
        ordering = ['skill__area','-level']


class BadgeType():
    WORK_SPEED = 'SP'
    REVIEW_SCORE = 'RS'
    NUMBER_OF_PROJECTS = 'PC'
    EARLY_USER = 'EU'

    def get_choices():
        return (
                    (BadgeType.WORK_SPEED, 'Fast work'),
                    (BadgeType.REVIEW_SCORE, 'Great reviews'),
                    (BadgeType.NUMBER_OF_PROJECTS, 'Completed projects'),
                    (BadgeType.EARLY_USER, 'Early user'),
                )

class BadgeTier():
    BASIC = 0
    ADVANCED = 1
    MASTER = 2

    def get_choices():
        return (
                    (BadgeTier.BASIC, 'Tier 1: basic'),
                    (BadgeTier.ADVANCED, 'Tier 2: advanced'),
                    (BadgeTier.MASTER, 'Tier 3: master'),
                )

class UserBadge(models.Model):
    type = models.CharField(
        max_length=2,
        choices=BadgeType.get_choices(),
        default=BadgeType.WORK_SPEED,
    )
    tier = models.IntegerField(
        verbose_name="Badge tier",
        help_text="How advanced this reward is.",
        choices = BadgeTier.get_choices(),
        default=BadgeTier.BASIC,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="User",
    )

    def is_tier_basic(self):
        return self.tier == BadgeTier.BASIC

    def is_tier_advanced(self):
        return self.tier == BadgeTier.ADVANCED

    def is_tier_master(self):
        return self.tier == BadgeTier.MASTER

    def is_type_work_speed(self):
        return self.type == BadgeType.WORK_SPEED

    def is_type_review_score(self):
        return self.type == BadgeType.REVIEW_SCORE

    def is_type_project_count(self):
        return self.type == BadgeType.NUMBER_OF_PROJECTS

    def is_type_early_user(self):
        return self.type == BadgeType.EARLY_USER

    class Meta:
        unique_together = ('user','type')
