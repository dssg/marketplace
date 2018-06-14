from django.db import models
from django_countries.fields import CountryField
from django.contrib.auth.models import AbstractUser
from dssgsolve import settings

from .common import (PHONE_REGEX, MAIN_CAUSE_CHOICES, CAUSE_EDUCATION,
                            ORGANIZATION_ROLE_CHOICES, ROLE_ORGANIZATION_STAFF,
                            REVIEW_RESULT_CHOICES, REVIEW_NEW)


class Organization(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=5000)
    logo_url = models.URLField(max_length=200, blank=True, null=True)
    website_url = models.URLField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(validators=[PHONE_REGEX], max_length=17, blank=True, null=True)
    email_address = models.EmailField()
    street_address = models.CharField(max_length=300)
    address_line_2 = models.CharField(max_length=300, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=20)
    country = CountryField()
    B100K = 'B000'
    B500K = 'B001'
    B1M = 'B005'
    B5M = 'B010'
    B20M = 'B050'
    B50M = 'B200'
    B50MP = 'B500'
    BUDGET_CHOICES = (
        (B100K, '<$100K'),
        (B500K, '$100K-$500K'),
        (B1M, '$500K-$1MM'),
        (B5M, '$1MM-$5MM'),
        (B20M, '$5MM-$20MM'),
        (B50M, '$20MM-$50MM'),
        (B50MP, '>$50MM')
    )
    budget = models.CharField(
        max_length=7,
        choices=BUDGET_CHOICES,
        default=B100K,
    )
    Y0 = 'Y00'
    Y1 = 'Y01'
    Y5 = 'Y05'
    Y10 = 'Y10'
    Y25 = 'Y25'
    OPERATION_YEARS_CHOICES = (
        (Y0, 'less than 1 year'),
        (Y1, '1 to 5 years'),
        (Y5, '5 to 10 years'),
        (Y10, '10 to 25 years'),
        (Y25, '25 or more years')
    )
    years_operation = models.CharField(
        max_length=3,
        choices=OPERATION_YEARS_CHOICES,
        default=Y0,
    )
    main_cause = models.CharField(
        max_length=2,
        choices=MAIN_CAUSE_CHOICES,
        default=CAUSE_EDUCATION,
    )
    LOCAL = 'LO'
    STATE = 'ST'
    REGION = 'RE'
    COUNTRY = 'CO'
    MULTINATIONAL = 'MN'
    OTHER = 'OT'
    ORGANIZATION_SCOPE_CHOICES = (
        (LOCAL, 'City/Local'),
        (STATE, 'State'),
        (REGION, 'Region (i.e. Midwest, Northeast, etc.)'),
        (COUNTRY, 'Country'),
        (MULTINATIONAL, 'Multi-national'),
        (OTHER, 'Other')
    )
    organization_scope = models.CharField(
        max_length=2,
        choices=ORGANIZATION_SCOPE_CHOICES,
        default=LOCAL,
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now= True)

    def __str__(self):
        return self.name

class OrganizationMembershipRequest(models.Model):
    role = models.IntegerField(choices = ORGANIZATION_ROLE_CHOICES, default=ROLE_ORGANIZATION_STAFF)
    status = models.CharField(max_length=3, choices=REVIEW_RESULT_CHOICES, default=REVIEW_NEW)
    public_reviewer_comments = models.TextField(max_length=5000, blank=True, null=True)
    private_reviewer_notes = models.TextField(max_length=5000, blank=True, null=True)
    request_date = models.DateTimeField(auto_now_add=True)
    resolution_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def is_new(self):
        return self.status == REVIEW_NEW

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == ACCEPTED and not self.user.is_organization_member(self.organization):
            new_role = OrganizationRole(role = self.role, user = self.user, organization = self.organization)
            new_role.save()
## TODO move this to the logic in the views?

class OrganizationRole(models.Model):
    role = models.IntegerField(choices = ORGANIZATION_ROLE_CHOICES, default=ROLE_ORGANIZATION_STAFF)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user','organization')
