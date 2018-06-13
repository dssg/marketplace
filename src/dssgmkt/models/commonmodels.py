from django.db import models
from django.core.validators import RegexValidator



EDUCATION = 'ED'
HEALTH = 'HE'
ENVIRONMENT = 'EN'
SOCIAL_SERVICES = 'SS'
TRANSPORTATION = 'TR'
ENERGY = 'EE'
INTERNATIONAL_DEVELOPMENT = 'ID'
PUBLIC_SAFETY = 'PS'
ECONOMIC_DEVELOPMENT = 'EC'
OTHER = 'OT'
MAIN_CAUSE_CHOICES = (
    (EDUCATION, 'Education'),
    (HEALTH, 'Health'),
    (ENVIRONMENT, 'Environment'),
    (SOCIAL_SERVICES, 'Social Services'),
    (TRANSPORTATION, 'Transportation'),
    (ENERGY, 'Energy and Environment'),
    (INTERNATIONAL_DEVELOPMENT, 'International development'),
    (PUBLIC_SAFETY, 'Public Safety'),
    (ECONOMIC_DEVELOPMENT, 'Economic Development'),
    (OTHER, 'Other')
)


NEW='NEW'
ACCEPTED='ACC'
REJECTED='REJ'
REVIEW_RESULT_CHOICES = (
    (NEW, 'Pending review'),
    (ACCEPTED, 'Accepted'),
    (REJECTED, 'Rejected')
)

BEGINNER = 0
INTERMEDIATE = 1
EXPERT = 2
SKILL_LEVEL_CHOICES = (
    (BEGINNER, 'Beginner'),
    (INTERMEDIATE, 'Intermediate'),
    (EXPERT, 'Expert')
)

ORGANIZATION_ADMINISTRATOR = 0
ORGANIZATION_STAFF = 1
ORGANIZATION_ROLE_CHOICES = (
    (ORGANIZATION_ADMINISTRATOR, 'Administrator'),
    (ORGANIZATION_STAFF, 'Staff')
)

PHONE_REGEX = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
