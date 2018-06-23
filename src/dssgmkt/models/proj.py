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
        verbose_name="Name",
        help_text="Name of this project. Make sure it is distinctive and recognizable on its own.",
        max_length=50,
    )
    short_summary = models.TextField(
        verbose_name="Short summary",
        help_text="Write a short description of the project that will be used as a summary of the project throughout the site.",
        max_length=1000,
    )
    motivation = models.TextField(
        verbose_name="Context/motivation/goals",
        help_text="Explain what is the context in which the project is needed, what is the motivation behind the project, and what are the goals of the project",
        max_length=5000,
        blank=True,
        null=True,
    )
    solution_description = models.TextField(
        verbose_name="Proposed solution",
        help_text="Describe what is the solution to the problem that will be build/created/deployed during this project.",
        max_length=5000,
        blank=True,
        null=True,
    )
    challenges = models.TextField(
        verbose_name="Main challenges",
        help_text="List the main challenges that you foresee in the project implementation. Remember to frame them so volunteers understand that this is an exciting project.",
        max_length=5000,
        blank=True,
        null=True,
    )
    banner_image_url = models.URLField(
        verbose_name="Project main image",
        help_text="A descriptive image identifying the project, it can be a project logo, an image representing the problem you want to solve, etc.",
        max_length=200,
        blank=True,
        null=True,
    )
    project_cause = models.CharField(
        verbose_name="Social cause",
        help_text="The main social good cause this project is framed under. If there are several that apply, pick the most relevant one.",
        max_length=2,
        choices=SocialCause.get_choices(),
        default=SocialCause.EDUCATION,
    )
    project_impact = models.TextField(
        verbose_name="",
        help_text="",
        max_length=5000,
        blank=True,
        null=True,
    )
    scoping_process = models.TextField(
        verbose_name="",
        help_text="",
        max_length=5000,
        blank=True,
        null=True,
    )
    available_staff = models.TextField(
        verbose_name="",
        help_text="",
        max_length=5000,
        blank=True,
        null=True,
    )
    available_data = models.TextField(
        verbose_name="",
        help_text="",
        max_length=5000,
        blank=True,
        null=True,
    )
    developer_agreement = models.TextField(
        verbose_name="Volunteer agreement",
        help_text="If you add an agreement, every volunteer that applies to the project will have to agree with those terms and conditions during their application process.",
        max_length=5000,
        blank=True,
        null=True,
    )
    intended_start_date = models.DateField(
        verbose_name="Start date",
        help_text="The planned start date of the project.",
    )
    intended_end_date = models.DateField(
        verbose_name="End date",
        help_text="The planned end date of the project.",
    )
    actual_start_date = models.DateField(
        verbose_name="Actual start date",
        help_text="The actual date this project started on.",
        blank=True,
        null=True,
    )
    actual_end_date = models.DateField(
        verbose_name="Actual end date",
        help_text="The actual date this project ended on.",
        blank=True,
        null=True,
    )
    status = models.CharField(
        verbose_name="Status",
        max_length=2,
        choices=ProjectStatus.get_choices(),
        default=ProjectStatus.DRAFT,
    )
    deliverable_github_url = models.URLField(
        verbose_name="Project github home",
        help_text="Link to the home page of the project in Github - it will be listed in the final deliverables of the project when the project ends.",
        max_length=200,
        blank=True,
        null=True,
    )
    deliverable_management_url = models.URLField(
        verbose_name="Project home page",
        help_text="Link to an external home page for this project, probably under your organization's website - it will be listed in the final deliverables of the project when the project ends.",
        max_length=200,
        blank=True,
        null=True,
    )
    deliverable_documentation_url = models.URLField(
        verbose_name="Documentation home",
        help_text="Link to an external repository for project documentation - it will be listed in the final deliverables of the project when the project ends.",
        max_length=200,
        blank=True,
        null=True,
    )
    deliverable_reports_url = models.URLField(
        verbose_name="Project reports home",
        help_text="Link to an external repository of project reports - it will be listed in the final deliverables of the project when the project ends.",
        max_length=200,
        blank=True,
        null=True,
    )
    creation_date = models.DateTimeField(
        verbose_name="Creation date",
        auto_now_add=True,
    )
    last_modified_date = models.DateTimeField(
        verbose_name="Last modification date",
        auto_now= True,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name="Organization",
        help_text="Organization that owns this project.",
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
    name = models.CharField(
        verbose_name="Name",
        help_text="Descriptive name that identifies the task within the project.",
        max_length=50,
    )
    description = models.TextField(
        verbose_name="Description",
        help_text="Describe in detail what the work for this task consists of, goals, methodologies, etc.",
        max_length=5000,
    )
    type = models.CharField(
        verbose_name="Task type",
        help_text="Different types of tasks have different roles within the project. Scoping tasks are needed to help new projects define the work that needs to be done. Project management tasks are used to guide the project from inception to finish. Domain work tasks include any data science work specified in the project.",
        max_length=3,
        choices=TaskType.get_choices(),
        default=TaskType.SCOPING_TASK,
    )
    onboarding_instructions = models.TextField(
        verbose_name="Volunteer onboarding instructions",
        help_text="Explain in detail everything a volunteer needs to know to work on this task. They will receive these instructions immediately after being accepted to work on this task, so make sure to be specific enough for volunteers to be able to work in the task after reading these instructions.",
        max_length=5000,
    )
    business_area = models.CharField(max_length=50)
    stage = models.CharField(
        verbose_name="Task status",
        max_length=3,
        choices=TaskStatus.get_choices(),
        default=TaskStatus.NOT_STARTED,
    )
    percentage_complete = models.FloatField()
    accepting_volunteers = models.BooleanField(
        verbose_name="Accepting volunteers?",
        help_text="Specify if volunteers can apply to this task at the moment or not.",
    )
    estimated_start_date = models.DateField(
        verbose_name="Start date",
        help_text="The planned start date for this specific task.",
    )
    estimated_end_date = models.DateField(
        verbose_name="End date",
        help_text="The planned end date for this specific task.",
    )
    actual_start_date = models.DateField(
        verbose_name="Actual start date",
        help_text="The actual date the work on this task started on.",
        blank=True,
        null=True,
    )
    actual_end_date = models.DateField(
        verbose_name="Actual end date",
        help_text="The actual date the work on this task finished on.",
        blank=True,
        null=True,
    )
    estimated_effort_hours = models.PositiveSmallIntegerField(
        verbose_name="Effort estimation (hours)",
        help_text="Give your best estimate of how many hours need to be spent on this task to finish it.",
        blank=True,
        null=True,
    )
    actual_effort_hours = models.PositiveSmallIntegerField(
        verbose_name="Actual effort (hours)",
        help_text="The actual number of hours that was spent in completing this task.",
        blank=True,
        null=True,
    )
    task_home_url = models.URLField(
        verbose_name="External task home URL",
        help_text="Link to an external home page for this task, that may contain additional documentation, data sets, etc.",
        max_length=200,
        blank=True,
        null=True,
    )
    task_deliverables_url = models.URLField(
        verbose_name="External deliverables URL",
        help_text="Link to a repository (Github, Bitbucket, etc.) where the volunteers will put the results of their work.",
        max_length = 200,
        blank=True,
        null=True,
    )
    creation_date = models.DateTimeField(
        verbose_name="Creation date",
        auto_now_add = True,
    )
    last_modified_date = models.DateTimeField(
        verbose_name="Last modification date",
        auto_now = True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name="Project",
        help_text="The project this task belongs to.",
    )

    def __str__(self):
        return self.name

    def is_in_progress(self):
        return self.stage == TaskStatus.STARTED

    def is_pending_review(self):
        return self.stage == TaskStatus.WAITING_REVIEW


class ProjectTaskReview(models.Model):
    volunteer_comment = models.TextField(
        verbose_name="Volunteer's comments",
        help_text="Type any comment, feedback or insights that you have about the work you did",
        max_length=2000,
        blank=True,
        null=True,
    )
    volunteer_effort_hours = models.PositiveSmallIntegerField(
        verbose_name="Effort spent (in hours)",
        help_text="How many hours did you spend in this work?",
    )
    reviewer_comment = models.TextField(
        verbose_name="Reviewer's comments",
        help_text="Add your feedback about the task. This is not private and will be shared with the volunteer.",
        max_length=2000,
        blank=True,
        null=True,
    )
    review_request_date = models.DateTimeField(
        verbose_name="Request date",
        help_text="Date the review request was created on by the volunter.",
        auto_now_add=True,
    )
    review_date = models.DateTimeField(
        verbose_name="Review date",
        help_text="Date the review was completed on.",
        blank=True,
        null=True,
    )
    review_result = models.CharField(
        verbose_name="Review result",
        help_text="Select if the task is accepted or rejected as completed (and specify why in the reviewer's comments).",
        max_length=3,
        choices=ReviewStatus.get_choices(),
        default=ReviewStatus.NEW,
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name="Task",
        help_text="Project task this review is related to.",
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
        verbose_name="Required expertise level",
        help_text="Minimum expertise level that the candidates should have in this skill to be suited for the task.",
        choices = SkillLevel.get_choices(),
        default=SkillLevel.BEGINNER,
    )

    importance = models.IntegerField(
        verbose_name="Importance",
        help_text="Grade of criticality that this skill has for the task completion. Candidates with lower expertise levels or lacking a skill will be more suited if that skill is rated of low importance for the task.",
        choices = TaskRequirementImportance.get_choices(),
        default=TaskRequirementImportance.NICE_TO_HAVE,
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        verbose_name="Skill",
        help_text="Specific skill requirement.",
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name="Task",
        help_text="Project task this requirement applies to.",
    )


class VolunteerApplication(models.Model):
    application_date = models.DateTimeField(
        verbose_name="Application Date",
        help_text="The date the volunteer applied on.",
        auto_now_add=True,
    )
    resolution_date = models.DateTimeField(
        verbose_name="Resolution date",
        help_text="The date the project staff accepted or rejected the volunteer's application.",
        blank=True,
        null=True,
    )
    status = models.CharField(
        verbose_name="Status",
        help_text="Specifies whether this application is new or if it has been accepted or rejected.",
        max_length=3,
        choices=ReviewStatus.get_choices(),
        default=ReviewStatus.NEW,
    )
    volunteer_application_letter = models.TextField(
        verbose_name="Application Letter",
        help_text="Introduce yourself and explain why you think you are the right candidate for working in this role.",
        max_length=5000,
    )
    public_reviewer_comments = models.TextField(
        verbose_name="Reviewer's comments",
        help_text="Tell the candidate the reason of the acceptance or rejection, and any other comment you want to add. This is not private and will be shared with the volunteer. ",
        max_length=5000,
        blank=True,
        null=True,
    )
    private_reviewer_notes = models.TextField(
        verbose_name="Private reviewer's notes",
        help_text="Private notes about the application. These notes will be shared with the rest of the project staff but not with the candidate or anybody else.",
        max_length=5000,
        blank=True,
        null=True,
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name="Task",
        help_text="The project task this application is related to.",
    )
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Applicant",
        help_text="The user applying to work on this task.",
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
        verbose_name="User role",
        # help_text="Role of this user in this specific project.",
        choices = ProjRole.get_choices(),
        default=ProjRole.STAFF,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Project member",
        # help_text="User member of this project.",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name="Project",
        # help_text="Project this role refers to.",
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
        verbose_name="User role",
        # help_text="Role of this user in this specific project task.",
        choices = TaskRole.get_choices(),
        default=TaskRole.VOLUNTEER,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Project task member",
        # help_text="User member of this project task.",
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name="Task",
        # help_text="Project task this role refers to.",
    )

    class Meta:
        unique_together = ('user','task')