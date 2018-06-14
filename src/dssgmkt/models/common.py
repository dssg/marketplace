from django.core.validators import RegexValidator
from django.db import models

class SocialCause():
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

    def get_choices():
        return (
                    (SocialCause.EDUCATION, 'Education'),
                    (SocialCause.HEALTH, 'Health'),
                    (SocialCause.ENVIRONMENT, 'Environment'),
                    (SocialCause.SOCIAL_SERVICES, 'Social Services'),
                    (SocialCause.TRANSPORTATION, 'Transportation'),
                    (SocialCause.ENERGY, 'Energy and Environment'),
                    (SocialCause.INTERNATIONAL_DEVELOPMENT, 'International development'),
                    (SocialCause.PUBLIC_SAFETY, 'Public Safety'),
                    (SocialCause.ECONOMIC_DEVELOPMENT, 'Economic Development'),
                    (SocialCause.OTHER, 'Other'),
                )

class ReviewStatus():
    NEW='NEW'
    ACCEPTED='ACC'
    REJECTED='REJ'

    def get_choices():
        return (
                (ReviewStatus.NEW, 'Pending review'),
                (ReviewStatus.ACCEPTED, 'Accepted'),
                (ReviewStatus.REJECTED, 'Rejected'),
                )

class SkillLevel():
    BEGINNER = 0
    INTERMEDIATE = 1
    EXPERT = 2

    def get_choices():
        return (
                    (SkillLevel.BEGINNER, 'Beginner'),
                    (SkillLevel.INTERMEDIATE, 'Intermediate'),
                    (SkillLevel.EXPERT, 'Expert'),
                )

class OrgRole():
    ADMINISTRATOR = 0
    STAFF = 1

    def get_choices():
        return (
                    (OrgRole.ADMINISTRATOR, 'Administrator'),
                    (OrgRole.STAFF, 'Staff')
                )

PHONE_REGEX = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
