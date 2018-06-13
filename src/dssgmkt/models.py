from django.db import models
from django_countries.fields import CountryField
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from dssgsolve import settings
# Create your models here.



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


class User(AbstractUser):
    DSSG_STAFF = 0
    VOLUNTEER = 1
    ORGANIZATION = 2
    USER_TYPE_CHOICES = (
        (DSSG_STAFF, 'Site staff'),
        (VOLUNTEER, 'Volunteer'),
        (ORGANIZATION, 'Organization member')
    )
    initial_type = models.IntegerField(choices = USER_TYPE_CHOICES, default=VOLUNTEER)
    skype_name = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(validators=[PHONE_REGEX], max_length=17, blank=True, null=True)
    special_code = models.CharField(max_length=20, blank=True, null=True)

    def is_organization_member(self, orgid):
        return self.organizationrole_set.filter(organization=orgid).exists()

    def is_organization_staff(self, orgid):
        return self.organizationrole_set.filter(organization=orgid, role=ORGANIZATION_STAFF).exists()

    def is_organization_admin(self, orgid):
        return self.organizationrole_set.filter(organization=orgid, role=ORGANIZATION_ADMINISTRATOR).exists()


class UserNotification(models.Model):
    notification_date = models.DateTimeField(auto_now_add=True)
    notification_description = models.CharField(max_length=500)
    is_read = models.BooleanField()
    INFO = 0
    WARNING = 1
    ALERT = 2
    NOTIFICATION_SEVERITY_CHOICES = (
        (INFO, 'Information'),
        (WARNING, 'Warning'),
        (ALERT, 'Alert')
    )
    severity = models.IntegerField(
        choices=NOTIFICATION_SEVERITY_CHOICES,
        default=INFO
    )
    GENERIC = 'GN'
    ORGANIZATION = 'OR'
    PROJECT = 'PJ'
    TASK = 'TK'
    VOLUNTEER_APPLICATION = 'VA'
    ORGANIZATION_MEMBERSHIP_REQUEST = 'OM'
    NOTIFICATION_SOURCE_CHOICES = (
        (GENERIC, 'Generic'),
        (ORGANIZATION, 'Organization'),
        (PROJECT, 'Project'),
        (TASK, 'Task'),
        (VOLUNTEER_APPLICATION, 'Volunteer application'),
        (ORGANIZATION_MEMBERSHIP_REQUEST, 'Organization membership request')
    )
    source = models.CharField(
        max_length=2,
        choices=NOTIFICATION_SOURCE_CHOICES,
        default=GENERIC
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class Skill(models.Model):
    area = models.CharField(max_length=50)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.area + "/" + self.name

    class Meta:
        unique_together = ('area','name')

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
        default=EDUCATION,
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


class Project(models.Model):
    name = models.CharField(max_length=50)
    short_summary = models.TextField(max_length=1000)
    motivation = models.TextField(max_length=5000, blank=True, null=True)
    solution_description = models.TextField(max_length=5000, blank=True, null=True)
    challenges = models.TextField(max_length=5000, blank=True, null=True)
    banner_image_url = models.URLField(max_length=200, blank=True, null=True)
    project_cause = models.CharField(
        max_length=2,
        choices=MAIN_CAUSE_CHOICES,
        default=EDUCATION,
    )
    project_impact = models.TextField(max_length=5000, blank=True, null=True)
    scoping_process = models.TextField(max_length=5000, blank=True, null=True)
    available_staff = models.TextField(max_length=5000, blank=True, null=True)
    available_data = models.TextField(max_length=5000, blank=True, null=True)
    developer_agreement = models.TextField(max_length=5000, blank=True, null=True)
    intended_start_date = models.DateField()
    intended_end_date = models.DateField()
    actual_start_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)
    DRAFT='DR'
    NEW='NW'
    DESIGN='DE'
    WAITING_DESIGN_APPROVAL='DA'
    WAITING_STAFF='WS'
    IN_PROGRESS='IP'
    WAITING_REVIEW='WR'
    COMPLETED='CO'
    EXPIRED='EX'
    DELETED='RM'
    STATUS_CHOICES = (
        (DRAFT, 'Draft'),
        (NEW, 'New'),
        (DESIGN, 'In scoping phase'),
        (WAITING_DESIGN_APPROVAL, 'Waiting for design review'),
        (WAITING_STAFF, 'Waiting for volunteers'),
        (IN_PROGRESS, 'In progress'),
        (WAITING_REVIEW, 'Waiting review'),
        (COMPLETED, 'Completed'),
        (EXPIRED, 'Expired'),
        (DELETED, 'Deleted')
    )
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default=DRAFT,
    )
    deliverable_github_url = models.URLField(max_length=200, blank=True, null=True)
    deliverable_management_url = models.URLField(max_length=200, blank=True, null=True)
    deliverable_documentation_url = models.URLField(max_length=200, blank=True, null=True)
    deliverable_reports_url = models.URLField(max_length=200, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now= True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def is_completed(self):
        return self.status == self.COMPLETED



class ProjectLog(models.Model):
    change_type = models.CharField(max_length=100)
    change_target = models.IntegerField()
    change_description = models.TextField(max_length=1000)
    change_date = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.change_date.strftime('%Y-%m-%d %H:%M') + ": " + self.change_description


class ProjectFollower(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user','project')


class ProjectTask(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=5000)

    SCOPING_TASK='SCT'
    PROJECT_MANAGEMENT_TASK='PMT'
    DOMAIN_WORK_TASK='DWT'
    PROJECT_TASK_TYPE_CHOICES = (
        (SCOPING_TASK, 'Project scoping'),
        (PROJECT_MANAGEMENT_TASK, 'Project management'),
        (DOMAIN_WORK_TASK, 'Domain work')
    )
    type = models.CharField(
        max_length=3,
        choices=PROJECT_TASK_TYPE_CHOICES,
        default=SCOPING_TASK,
    )
    onboarding_instructions = models.TextField(max_length=5000)
    business_area = models.CharField(max_length=50)

    NOT_STARTED='NOT'
    ACCEPTING_VOLUNTEERS='AVL'
    STARTED='STA'
    WAITING_REVIEW='PRW'
    COMPLETED='COM'
    DELETED='DEL'
    PROJECT_TASK_STAGE_CHOICES = (
        (NOT_STARTED, 'Not started'),
        (ACCEPTING_VOLUNTEERS, 'Accepting volunteers'),
        (STARTED, 'Started'),
        (WAITING_REVIEW, 'Pending review'),
        (COMPLETED, 'Completed'),
        (DELETED, 'Deleted')
    )
    stage = models.CharField(
        max_length=3,
        choices=PROJECT_TASK_STAGE_CHOICES,
        default=NOT_STARTED,
    )
    percentage_complete = models.FloatField()
    accepting_volunteers = models.BooleanField()

    estimated_start_date = models.DateField()
    estimated_end_date = models.DateField()
    actual_start_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)

    estimated_effort_hours = models.IntegerField(blank=True, null=True)
    actual_effort_hours = models.IntegerField(blank=True, null=True)
    task_home_url = models.URLField(max_length=200, blank=True, null=True)
    task_deliverables_url = models.URLField(max_length = 200, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add = True)
    last_modified_date = models.DateTimeField(auto_now = True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def is_in_progress(self):
        return self.stage == self.STARTED

    def is_pending_review(self):
        return self.stage == self.WAITING_REVIEW


class ProjectTaskReview(models.Model):
    volunteer_comment = models.TextField(max_length=2000, blank=True, null=True)
    volunteer_effort_hours = models.IntegerField()
    reviewer_comment = models.TextField(max_length=2000, blank=True, null=True)
    review_request_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(blank=True, null=True)
    review_result = models.CharField(
        max_length=3,
        choices=REVIEW_RESULT_CHOICES,
        default=NEW,
    )
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE)

class ProjectTaskRequirement(models.Model):
    level = models.IntegerField(choices = SKILL_LEVEL_CHOICES, default=BEGINNER)
    NICE_TO_HAVE = 0
    IMPORTANT = 1
    REQUIRED = 2
    IMPORTANCE_CHOICES = (
        (NICE_TO_HAVE, 'Nice to have'),
        (IMPORTANT, 'Important'),
        (REQUIRED, 'Required')
    )
    importance = models.IntegerField(choices = IMPORTANCE_CHOICES, default=NICE_TO_HAVE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE)


class VolunteerApplication(models.Model):
    application_date = models.DateTimeField(auto_now_add=True)
    resolution_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=3,
        choices=REVIEW_RESULT_CHOICES,
        default=NEW,
    )
    volunteer_application_letter = models.TextField(max_length=5000)
    public_reviewer_comments = models.TextField(max_length=5000, blank=True, null=True)
    private_reviewer_notes = models.TextField(max_length=5000, blank=True, null=True)
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def is_new(self):
        return self.status == NEW


class VolunteerProfile(models.Model):
    portfolio_url = models.URLField(max_length=200, blank=True, null=True)
    github_url = models.URLField(max_length=200, blank=True, null=True)
    linkedin_url = models.URLField(max_length=200, blank=True, null=True)
    degree_name = models.CharField(max_length=50, blank=True, null=True)
    BACHELORS = 0
    MASTERS = 1
    PHD = 2
    DEGREE_LEVEL_CHOICES = (
        (BACHELORS, 'Bachelor\'s'),
        (MASTERS, 'Master\'s'),
        (PHD, 'PhD')
    )
    degree_level = models.IntegerField(choices = DEGREE_LEVEL_CHOICES, default=BACHELORS)
    university = models.CharField(max_length=50, blank=True, null=True)
    cover_letter = models.TextField(max_length=2000, blank=True, null=True)
    weekly_availability_hours = models.IntegerField()
    availability_start_date = models.DateField(blank=True, null=True)
    availability_end_date = models.DateField(blank=True, null=True)
    volunteer_status = models.CharField(max_length=3, choices=REVIEW_RESULT_CHOICES, default=NEW)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class VolunteerSkill(models.Model):
    level = models.IntegerField(choices = SKILL_LEVEL_CHOICES, default=BEGINNER)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user','skill')

class OrganizationMembershipRequest(models.Model):
    role = models.IntegerField(choices = ORGANIZATION_ROLE_CHOICES, default=ORGANIZATION_STAFF)
    status = models.CharField(max_length=3, choices=REVIEW_RESULT_CHOICES, default=NEW)
    public_reviewer_comments = models.TextField(max_length=5000, blank=True, null=True)
    private_reviewer_notes = models.TextField(max_length=5000, blank=True, null=True)
    request_date = models.DateTimeField(auto_now_add=True)
    resolution_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def is_new(self):
        return self.status == NEW

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == ACCEPTED and not self.user.is_organization_member(self.organization):
            new_role = OrganizationRole(role = self.role, user = self.user, organization = self.organization)
            new_role.save()
## TODO move this to the logic in the views?

class OrganizationRole(models.Model):
    role = models.IntegerField(choices = ORGANIZATION_ROLE_CHOICES, default=ORGANIZATION_STAFF)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user','organization')

class ProjectRole(models.Model):
    PROJECT_OWNER = 0
    PROJECT_STAFF = 1
    PROJECT_ROLE_CHOICES = (
        (PROJECT_OWNER, 'Owner'),
        (PROJECT_STAFF, 'Staff')
    )
    role = models.IntegerField(choices = PROJECT_ROLE_CHOICES, default=PROJECT_STAFF)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user','project')

class ProjectTaskRole(models.Model):
    TASK_VOLUNTEER = 0
    TASK_ROLE_CHOICES = (
        (TASK_VOLUNTEER, 'Volunteer'),
    )
    role = models.IntegerField(choices = TASK_ROLE_CHOICES, default=TASK_VOLUNTEER)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user','task')
