from django.core.validators import RegexValidator
from django.db import models

CAUSE_EDUCATION = 'ED'
CAUSE_HEALTH = 'HE'
CAUSE_ENVIRONMENT = 'EN'
CAUSE_SOCIAL_SERVICES = 'SS'
CAUSE_TRANSPORTATION = 'TR'
CAUSE_ENERGY = 'EE'
CAUSE_INTERNATIONAL_DEVELOPMENT = 'ID'
CAUSE_PUBLIC_SAFETY = 'PS'
CAUSE_ECONOMIC_DEVELOPMENT = 'EC'
CAUSE_OTHER = 'OT'
MAIN_CAUSE_CHOICES = (
    (CAUSE_EDUCATION, 'Education'),
    (CAUSE_HEALTH, 'Health'),
    (CAUSE_ENVIRONMENT, 'Environment'),
    (CAUSE_SOCIAL_SERVICES, 'Social Services'),
    (CAUSE_TRANSPORTATION, 'Transportation'),
    (CAUSE_ENERGY, 'Energy and Environment'),
    (CAUSE_INTERNATIONAL_DEVELOPMENT, 'International development'),
    (CAUSE_PUBLIC_SAFETY, 'Public Safety'),
    (CAUSE_ECONOMIC_DEVELOPMENT, 'Economic Development'),
    (CAUSE_OTHER, 'Other')
)


REVIEW_NEW='NEW'
REVIEW_ACCEPTED='ACC'
REVIEW_REJECTED='REJ'
REVIEW_RESULT_CHOICES = (
    (REVIEW_NEW, 'Pending review'),
    (REVIEW_ACCEPTED, 'Accepted'),
    (REVIEW_REJECTED, 'Rejected')
)

SKILL_LEVEL_BEGINNER = 0
SKILL_LEVEL_INTERMEDIATE = 1
SKILL_LEVEL_EXPERT = 2
SKILL_LEVEL_CHOICES = (
    (SKILL_LEVEL_BEGINNER, 'Beginner'),
    (SKILL_LEVEL_INTERMEDIATE, 'Intermediate'),
    (SKILL_LEVEL_EXPERT, 'Expert')
)

ROLE_ORGANIZATION_ADMINISTRATOR = 0
ROLE_ORGANIZATION_STAFF = 1
ORGANIZATION_ROLE_CHOICES = (
    (ROLE_ORGANIZATION_ADMINISTRATOR, 'Administrator'),
    (ROLE_ORGANIZATION_STAFF, 'Staff')
)

PHONE_REGEX = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
