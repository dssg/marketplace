from django.db import models
from django_countries.fields import CountryField

from dssgsolve import settings

from .common import (
    SocialCause, ReviewStatus, PHONE_REGEX,
    SkillLevel
)
from .org import Organization
from .user import Skill

class ProjectStatus():
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

    def get_choices():
        return (
                    (ProjectStatus.DRAFT, 'Draft'),
                    (ProjectStatus.NEW, 'New'),
                    (ProjectStatus.DESIGN, 'In scoping phase'),
                    (ProjectStatus.WAITING_DESIGN_APPROVAL, 'Waiting for design review'),
                    (ProjectStatus.WAITING_STAFF, 'Waiting for volunteers'),
                    (ProjectStatus.IN_PROGRESS, 'In progress'),
                    (ProjectStatus.WAITING_REVIEW, 'Waiting review'),
                    (ProjectStatus.COMPLETED, 'Completed'),
                    (ProjectStatus.EXPIRED, 'Expired'),
                    (ProjectStatus.DELETED, 'Deleted')
                )

class Project(models.Model):
    name = models.CharField(
        max_length=50,
    )
    short_summary = models.TextField(
        max_length=1000,
    )
    motivation = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    solution_description = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    challenges = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    banner_image_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    project_cause = models.CharField(
        max_length=2,
        choices=SocialCause.get_choices(),
        default=SocialCause.EDUCATION,
    )
    project_impact = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    scoping_process = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    available_staff = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    available_data = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    developer_agreement = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    intended_start_date = models.DateField()
    intended_end_date = models.DateField()
    actual_start_date = models.DateField(
        blank=True,
        null=True,
    )
    actual_end_date = models.DateField(
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=2,
        choices=ProjectStatus.get_choices(),
        default=ProjectStatus.DRAFT,
    )
    deliverable_github_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    deliverable_management_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    deliverable_documentation_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    deliverable_reports_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now= True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name

    def is_completed(self):
        return self.status == ProjectStatus.COMPLETED



class ProjectLog(models.Model):
    change_type = models.CharField(max_length=100)
    change_target = models.IntegerField()
    change_description = models.TextField(max_length=1000)
    change_date = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.change_date.strftime('%Y-%m-%d %H:%M') + ": " + self.change_description


class ProjectFollower(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ('user','project')

class TaskType():
    SCOPING_TASK='SCT'
    PROJECT_MANAGEMENT_TASK='PMT'
    DOMAIN_WORK_TASK='DWT'

    def get_choices():
        return (
                    (TaskType.SCOPING_TASK, 'Project scoping'),
                    (TaskType.PROJECT_MANAGEMENT_TASK, 'Project management'),
                    (TaskType.DOMAIN_WORK_TASK, 'Domain work')
                )

class TaskStatus():
    NOT_STARTED='NOT'
    ACCEPTING_VOLUNTEERS='AVL'
    STARTED='STA'
    WAITING_REVIEW='PRW'
    COMPLETED='COM'
    DELETED='DEL'

    def get_choices():
        return (
                    (TaskStatus.NOT_STARTED, 'Not started'),
                    (TaskStatus.ACCEPTING_VOLUNTEERS, 'Accepting volunteers'),
                    (TaskStatus.STARTED, 'Started'),
                    (TaskStatus.WAITING_REVIEW, 'Pending review'),
                    (TaskStatus.COMPLETED, 'Completed'),
                    (TaskStatus.DELETED, 'Deleted')
                )

class ProjectTask(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=5000)
    type = models.CharField(
        max_length=3,
        choices=TaskType.get_choices(),
        default=TaskType.SCOPING_TASK,
    )
    onboarding_instructions = models.TextField(max_length=5000)
    business_area = models.CharField(max_length=50)
    stage = models.CharField(
        max_length=3,
        choices=TaskStatus.get_choices(),
        default=TaskStatus.NOT_STARTED,
    )
    percentage_complete = models.FloatField()
    accepting_volunteers = models.BooleanField()
    estimated_start_date = models.DateField()
    estimated_end_date = models.DateField()
    actual_start_date = models.DateField(
        blank=True,
        null=True,
    )
    actual_end_date = models.DateField(
        blank=True,
        null=True,
    )
    estimated_effort_hours = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
    )
    actual_effort_hours = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
    )
    task_home_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    task_deliverables_url = models.URLField(
        max_length = 200,
        blank=True,
        null=True,
    )
    creation_date = models.DateTimeField(auto_now_add = True)
    last_modified_date = models.DateTimeField(auto_now = True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name

    def is_in_progress(self):
        return self.stage == self.STARTED

    def is_pending_review(self):
        return self.stage == self.WAITING_REVIEW


class ProjectTaskReview(models.Model):
    volunteer_comment = models.TextField(
        max_length=2000,
        blank=True,
        null=True,
    )
    volunteer_effort_hours = models.PositiveSmallIntegerField()
    reviewer_comment = models.TextField(
        max_length=2000,
        blank=True,
        null=True,
    )
    review_request_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    review_result = models.CharField(
        max_length=3,
        choices=ReviewStatus.get_choices(),
        default=ReviewStatus.NEW,
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
    )

class TaskRequirementImportance():
    NICE_TO_HAVE = 0
    IMPORTANT = 1
    REQUIRED = 2

    def get_choices():
        return (
                    (TaskRequirementImportance.NICE_TO_HAVE, 'Nice to have'),
                    (TaskRequirementImportance.IMPORTANT, 'Important'),
                    (TaskRequirementImportance.REQUIRED, 'Required')
                )

class ProjectTaskRequirement(models.Model):
    level = models.IntegerField(
        choices = SkillLevel.get_choices(),
        default=SkillLevel.BEGINNER,
    )

    importance = models.IntegerField(
        choices = TaskRequirementImportance.get_choices(),
        default=TaskRequirementImportance.NICE_TO_HAVE,
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
    )


class VolunteerApplication(models.Model):
    application_date = models.DateTimeField(auto_now_add=True)
    resolution_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=3,
        choices=ReviewStatus.get_choices(),
        default=ReviewStatus.NEW,
    )
    volunteer_application_letter = models.TextField(max_length=5000)
    public_reviewer_comments = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    private_reviewer_notes = models.TextField(
        max_length=5000,
        blank=True,
        null=True,
    )
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def is_new(self):
        return self.status == ReviewStatus.NEW

class ProjRole():
    OWNER = 0
    STAFF = 1

    def get_choices():
        return (
                    (ProjRole.OWNER, 'Owner'),
                    (ProjRole.STAFF, 'Staff')
                )

class ProjectRole(models.Model):
    role = models.IntegerField(
        choices = ProjRole.get_choices(),
        default=ProjRole.STAFF,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ('user','project')

class TaskRole():
    VOLUNTEER = 0

    def get_choices():
        return (
                    (TaskRole.VOLUNTEER, 'Volunteer'),
                )

class ProjectTaskRole(models.Model):
    role = models.IntegerField(
        choices = TaskRole.get_choices(),
        default=TaskRole.VOLUNTEER,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ('user','task')
