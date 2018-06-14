from django.db import models
from django_countries.fields import CountryField

from dssgsolve import settings

from .common import (CAUSE_EDUCATION, MAIN_CAUSE_CHOICES, PHONE_REGEX,
                     REVIEW_NEW, REVIEW_RESULT_CHOICES, SKILL_LEVEL_BEGINNER,
                     SKILL_LEVEL_CHOICES)
from .org import Organization
from .user import Skill


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
        default=CAUSE_EDUCATION,
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
        default=REVIEW_NEW,
    )
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE)

class ProjectTaskRequirement(models.Model):
    level = models.IntegerField(choices = SKILL_LEVEL_CHOICES, default=SKILL_LEVEL_BEGINNER)
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
        default=REVIEW_NEW,
    )
    volunteer_application_letter = models.TextField(max_length=5000)
    public_reviewer_comments = models.TextField(max_length=5000, blank=True, null=True)
    private_reviewer_notes = models.TextField(max_length=5000, blank=True, null=True)
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def is_new(self):
        return self.status == REVIEW_NEW

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
