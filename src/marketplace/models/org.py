from django.conf import settings
from django.db import models
from django_countries.fields import CountryField
from django.utils.safestring import mark_safe

from .common import SocialCause, ReviewStatus, OrgRole, validate_image_size


class Budget():
    B100K = 'B000'
    B500K = 'B001'
    B1M = 'B005'
    B5M = 'B010'
    B20M = 'B050'
    B50M = 'B200'
    B50MP = 'B500'

    def get_choices():
        return (
                    (Budget.B100K, '<$100K'),
                    (Budget.B500K, '$100K-$500K'),
                    (Budget.B1M, '$500K-$1MM'),
                    (Budget.B5M, '$1MM-$5MM'),
                    (Budget.B20M, '$5MM-$20MM'),
                    (Budget.B50M, '$20MM-$50MM'),
                    (Budget.B50MP, '>$50MM')
                )

class YearsInOperation():
    Y0 = 'Y00'
    Y1 = 'Y01'
    Y5 = 'Y05'
    Y10 = 'Y10'
    Y25 = 'Y25'

    def get_choices():
        return (
            (YearsInOperation.Y0, 'less than 1 year'),
            (YearsInOperation.Y1, '1 to 5 years'),
            (YearsInOperation.Y5, '5 to 10 years'),
            (YearsInOperation.Y10, '10 to 25 years'),
            (YearsInOperation.Y25, '25 or more years')
        )

class GeographicalScope():
    LOCAL = 'LO'
    STATE = 'ST'
    REGION = 'RE'
    COUNTRY = 'CO'
    MULTINATIONAL = 'MN'
    OTHER = 'OT'

    def get_choices():
        return (
            (GeographicalScope.LOCAL, 'City/Local'),
            (GeographicalScope.STATE, 'State'),
            (GeographicalScope.REGION, 'Region (i.e. Midwest, Northeast, etc.)'),
            (GeographicalScope.COUNTRY, 'Country'),
            (GeographicalScope.MULTINATIONAL, 'Multi-national'),
            (GeographicalScope.OTHER, 'Other')
        )

class OrganizationType():
    SOCIAL_GOOD = 'SGP'
    VOLUNTEER = 'VOL'

    def get_choices():
        return (
            (OrganizationType.SOCIAL_GOOD, 'Social good organization'),
            (OrganizationType.VOLUNTEER, 'Volunteer group'),
        )

class Organization(models.Model):

    name = models.CharField(
        max_length=200,
        verbose_name="Organization name",
        help_text="Type the name of your organization.",
    )
    type = models.CharField(
        verbose_name="Organization type",
        max_length=3,
        choices=OrganizationType.get_choices(),
        default=OrganizationType.SOCIAL_GOOD,
    )
    short_summary = models.TextField(
        verbose_name="Short summary",
        help_text="Write a short description of the organization that will be used throughout the site when needing a compact description.",
        max_length=1000,
    )
    description = models.TextField(
        max_length=5000,
        verbose_name="Organization description",
        help_text="Write a description for volunteers to understand the context of your projects.",
    )
    logo_url = models.URLField(
        verbose_name="Organization logo URL",
        help_text="URL of an external image file that represents your organization",
        blank=True,
        null=True,
    )
    logo_file = models.ImageField(
        verbose_name="Organization logo",
        help_text="Upload an image file that represents your organization",
        upload_to="orglogos/",
        blank=True,
        null=True,
        validators=[validate_image_size],
    )
    website_url = models.URLField(
        verbose_name="External website URL",
        help_text="Add a link to your organization's home page so volunteers can reach you",
        max_length=200,
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
    email_address = models.EmailField(
        verbose_name="Contact email",
        blank=True,
    )
    street_address = models.CharField(
        verbose_name="Address line 1",
        max_length=300,
    )
    address_line_2 = models.CharField(
        verbose_name="Address line 2",
        max_length=300,
        blank=True,
        null=True,
    )
    city = models.CharField(
        verbose_name="City",
        max_length=100,
    )
    state = models.CharField(
        verbose_name="State/Province",
        max_length=100,
    )
    zipcode = models.CharField(
        verbose_name="ZIP/Postal code",
        max_length=20,
    )
    country = CountryField(verbose_name="Country")
    budget = models.CharField(
        verbose_name="Yearly budget",
        help_text="Select the budget range that fits your organization best",
        max_length=7,
        choices=Budget.get_choices(),
        default=Budget.B100K,
    )
    years_operation = models.CharField(
        verbose_name="Years in operation",
        help_text="For how long has the organization been in operation?",
        max_length=3,
        choices=YearsInOperation.get_choices(),
        default=YearsInOperation.Y0,
    )
    main_cause = models.CharField(
        verbose_name="Main social cause",
        help_text="What is the main social cause that this organization has as a goal?",
        max_length=2,
        choices=SocialCause.get_choices(),
        default=SocialCause.EDUCATION,
    )
    organization_scope = models.CharField(
        verbose_name="Geographical scope",
        help_text="What is the geographical scope that this organization targets?",
        max_length=2,
        choices=GeographicalScope.get_choices(),
        default=GeographicalScope.LOCAL,
    )
    is_demo = models.BooleanField(
        verbose_name="Demo organization?",
        help_text="Specifies if this is a demonstration organization",
        default=False,
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now= True)

    def is_social_cause_education(self):
        return self.main_cause == SocialCause.EDUCATION

    def is_social_cause_health(self):
        return self.main_cause == SocialCause.HEALTH

    def is_social_cause_environment(self):
        return self.main_cause == SocialCause.ENVIRONMENT

    def is_social_cause_social_services(self):
        return self.main_cause == SocialCause.SOCIAL_SERVICES

    def is_social_cause_transportation(self):
        return self.main_cause == SocialCause.TRANSPORTATION

    def is_social_cause_energy(self):
        return self.main_cause == SocialCause.ENERGY

    def is_social_cause_internantional_dev(self):
        return self.main_cause == SocialCause.INTERNATIONAL_DEVELOPMENT

    def is_social_cause_public_safety(self):
        return self.main_cause == SocialCause.PUBLIC_SAFETY

    def is_social_cause_economic_dev(self):
        return self.main_cause == SocialCause.ECONOMIC_DEVELOPMENT

    def is_social_cause_other(self):
        return self.main_cause == SocialCause.OTHER

    def is_volunteer_group(self):
        return self.type == OrganizationType.VOLUNTEER

    def is_social_good_organization(self):
        return self.type == OrganizationType.SOCIAL_GOOD
        
    def __str__(self):
        return self.name

class OrganizationMembershipRequest(models.Model):
    role = models.IntegerField(
        verbose_name="User role",
        help_text=mark_safe("Select the role of this user in the organization. <strong>IMPORTANT: Administrators will have full permissions over the organization</strong> so only assign this permission if you are sure you want to grant this user full control of the organization."),
        choices = OrgRole.get_choices(),
        default=OrgRole.STAFF,
    )
    status = models.CharField(
        verbose_name="Membership request status",
        max_length=3,
        choices=ReviewStatus.get_choices(),
        default=ReviewStatus.NEW,
    )
    public_reviewer_comments = models.TextField(
        verbose_name="Public reviewer comments",
        help_text=mark_safe("Write any comments you have for the applicant. <strong>IMPORTANT: These comments will be public and can be viewed by users outside ot the organization.</strong>"),
        max_length=5000,
        blank=True,
        null=True,
    )
    private_reviewer_notes = models.TextField(
        verbose_name="Private review notes",
        help_text=mark_safe("Write any private comments regarding this decision. <strong>IMPORTANT: these notes are private to the organization, but all members of the organization will be able to see them.</strong>"),
        max_length=5000,
        blank=True,
        null=True,
    )
    request_date = models.DateTimeField(
        verbose_name="Review date",
        help_text="Date and time in which the membership request was created",
        auto_now_add=True,
    )
    resolution_date = models.DateTimeField(
        verbose_name="Resolution date",
        help_text="Date and time in which the membership request was resolved",
        auto_now=True,
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Membership applicant",
        help_text="User that requested membership in this organization",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Review author",
        help_text="User that reviewed the membership application",
        related_name="reviewed_organization_membership_request",
        blank=True,
        null=True,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name="Organization",
        help_text="Organization to which the user is applying to be member of",
    )

    def is_new(self):
        return self.status == ReviewStatus.NEW

    def is_accepted(self):
        return self.status == ReviewStatus.ACCEPTED

    def is_rejected(self):
        return self.status == ReviewStatus.REJECTED



class OrganizationRole(models.Model):
    role = models.IntegerField(
        verbose_name="User role",
        # help_text="Role of this user in this specific organization.",
        choices = OrgRole.get_choices(),
        default=OrgRole.STAFF,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Organization member",
        # help_text="User member of this organization.",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name="Organization",
        # help_text="Organization this membership refers to.",
    )
    creation_date = models.DateTimeField(
        verbose_name="Creation date",
        help_text="Date and time in which the organization role was created",
        auto_now_add=True,
    )

    class Meta:
        unique_together = ('user','organization')

class OrganizationSocialCause(models.Model):
    social_cause = models.CharField(
        verbose_name="Social cause",
        help_text="What is the social cause that this organization has as a goal?",
        max_length=2,
        choices=SocialCause.get_choices(),
        default=SocialCause.EDUCATION,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name="Organization",
        # help_text="Organization this membership refers to.",
    )

    def is_social_cause_education(self):
        return self.social_cause == SocialCause.EDUCATION

    def is_social_cause_health(self):
        return self.social_cause == SocialCause.HEALTH

    def is_social_cause_environment(self):
        return self.social_cause == SocialCause.ENVIRONMENT

    def is_social_cause_social_services(self):
        return self.social_cause == SocialCause.SOCIAL_SERVICES

    def is_social_cause_transportation(self):
        return self.social_cause == SocialCause.TRANSPORTATION

    def is_social_cause_energy(self):
        return self.social_cause == SocialCause.ENERGY

    def is_social_cause_internantional_dev(self):
        return self.social_cause == SocialCause.INTERNATIONAL_DEVELOPMENT

    def is_social_cause_public_safety(self):
        return self.social_cause == SocialCause.PUBLIC_SAFETY

    def is_social_cause_economic_dev(self):
        return self.social_cause == SocialCause.ECONOMIC_DEVELOPMENT

    def is_social_cause_other(self):
        return self.social_cause == SocialCause.OTHER

    def __str__(self):
        return self.get_social_cause_display()

    class Meta:
        unique_together = ('social_cause','organization')
