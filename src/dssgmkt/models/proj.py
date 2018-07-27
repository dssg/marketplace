from django.db import models
from django_countries.fields import CountryField

from dssgsolve import settings

from .common import (
    SocialCause, ReviewStatus, Score,
    SkillLevel, validate_image_size,
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
        max_length=200,
    )
    short_summary = models.TextField(
        verbose_name="Short summary",
        help_text="Write a short description of the project that will be used throughout the site when needing a compact description.",
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
    banner_image_file = models.ImageField(
        verbose_name="Project main image",
        help_text="A descriptive image identifying the project, it can be a project logo, an image representing the problem you want to solve, etc.",
        upload_to="projlogos/",
        blank=True,
        null=True,
        validators=[validate_image_size],
    )
    project_cause = models.CharField(
        verbose_name="Social cause",
        help_text="The main social good cause this project is framed under. If there are several that apply, pick the most relevant one.",
        max_length=2,
        choices=SocialCause.get_choices(),
        default=SocialCause.EDUCATION,
    )
    project_impact = models.TextField(
        verbose_name="Project impact",
        help_text="How critical is this project for your organization? How you're solving this problem today? What's the impact if this project is completed successfully?",
        max_length=5000,
        blank=True,
        null=True,
    )
    scoping_process = models.TextField(
        verbose_name="Scoping process",
        help_text="Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)",
        max_length=5000,
        blank=True,
        null=True,
    )
    available_staff = models.TextField(
        verbose_name="Available staff",
        help_text="Who from your organization would be available to provide assistance (approximately 1-3 hours per week) throughout the summer? (Technical staff, subject matter experts, etc.)",
        max_length=5000,
        blank=True,
        null=True,
    )
    available_data = models.TextField(
        verbose_name="Available data",
        help_text="Describe the data available to use for this project. (Size, variables, completeness, availability, privacy, etc.)",
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
    deliverables_description = models.TextField(
        verbose_name="Deliverables page description",
        help_text="Once the project is completed, the resulting deliverables will be presented in a separate page. This description will be placed at the top of the deliverables page, so you can describe if the goals of the project were met, how to interpret the results, where the different artifacts of the project are stored, etc.",
        max_length=5000,
        blank=True,
        null=True,
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

    def is_draft_status(self):
        return self.status == ProjectStatus.DRAFT

    def is_new_status(self):
        return self.status == ProjectStatus.NEW

    def is_design_status(self):
        return self.status == ProjectStatus.DESIGN

    def is_waiting_design_approval_status(self):
        return self.status == ProjectStatus.WAITING_DESIGN_APPROVAL

    def is_waiting_staff_status(self):
        return self.status == ProjectStatus.WAITING_STAFF

    def is_in_progress_status(self):
        return self.status == ProjectStatus.IN_PROGRESS

    def is_waiting_review_status(self):
        return self.status == ProjectStatus.WAITING_REVIEW

    def is_completed_status(self):
        return self.status == ProjectStatus.COMPLETED

    def is_expired_status(self):
        return self.status == ProjectStatus.EXPIRED

    def is_social_cause_education(self):
        return self.project_cause == SocialCause.EDUCATION

    def is_social_cause_health(self):
        return self.project_cause == SocialCause.HEALTH

    def is_social_cause_environment(self):
        return self.project_cause == SocialCause.ENVIRONMENT

    def is_social_cause_social_services(self):
        return self.project_cause == SocialCause.SOCIAL_SERVICES

    def is_social_cause_transportation(self):
        return self.project_cause == SocialCause.TRANSPORTATION

    def is_social_cause_energy(self):
        return self.project_cause == SocialCause.ENERGY

    def is_social_cause_internantional_dev(self):
        return self.project_cause == SocialCause.INTERNATIONAL_DEVELOPMENT

    def is_social_cause_public_safety(self):
        return self.project_cause == SocialCause.PUBLIC_SAFETY

    def is_social_cause_economic_dev(self):
        return self.project_cause == SocialCause.ECONOMIC_DEVELOPMENT

    def is_social_cause_other(self):
        return self.project_cause == SocialCause.OTHER

class ProjectScope(models.Model):
    scope = models.TextField(
        verbose_name="Project scope",
        help_text="The detailed scope of the project.",
        max_length=5000,
        blank=True,
        null=True,
    )
    project_impact = models.TextField(
        verbose_name="Project impact",
        help_text="How critical is this project for your organization? How you're solving this problem today? What's the impact if this project is completed successfully?",
        max_length=5000,
        blank=True,
        null=True,
    )
    scoping_process = models.TextField(
        verbose_name="Scoping process",
        help_text="Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)",
        max_length=5000,
        blank=True,
        null=True,
    )
    available_staff = models.TextField(
        verbose_name="Available staff",
        help_text="Who from your organization would be available to provide assistance (approximately 1-3 hours per week) throughout the summer? (Technical staff, subject matter experts, etc.)",
        max_length=5000,
        blank=True,
        null=True,
    )
    available_data = models.TextField(
        verbose_name="Available data",
        help_text="Describe the data available to use for this project. (Size, variables, completeness, availability, privacy, etc.)",
        max_length=5000,
        blank=True,
        null=True,
    )
    version_notes = models.TextField(
        verbose_name="New version notes",
        help_text="Type the reason the scope is being modified and describe the changes made.",
        max_length=5000,
    )
    creation_date = models.DateTimeField(
        verbose_name="Creation date",
        auto_now_add=True,
    )
    is_current = models.BooleanField(
        verbose_name="Is current?",
        help_text="Specifies if this is the latest scope of the project.",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

class ProjectLogSource():
    VOLUNTEER_APPLICATION = 'VA'
    STAFF = 'ST'
    TASK = 'TK'
    TASK_REVIEW = 'TK'
    VOLUNTEER = 'VO'
    STATUS = 'SU'
    INFORMATION = 'IN'
    SCOPE = 'SC'

    def get_choices():
        return (
                    (ProjectLogSource.TASK, 'Task'),
                    (ProjectLogSource.VOLUNTEER_APPLICATION, 'Volunteer application'),
                    (ProjectLogSource.STAFF, 'Staff'),
                    (ProjectLogSource.TASK_REVIEW, 'Task review'),
                    (ProjectLogSource.VOLUNTEER, 'Volunteer'),
                    (ProjectLogSource.STATUS, 'Status'),
                    (ProjectLogSource.INFORMATION, 'Information'),
                    (ProjectLogSource.SCOPE, 'Scope'),
                )

class ProjectLogType():
    ADD = 'AD'
    REMOVE = 'RM'
    EDIT = 'ED'
    COMPLETE = 'FN'

    def get_choices():
        return (
                    (ProjectLogType.ADD, 'Added'),
                    (ProjectLogType.REMOVE, 'Removed'),
                    (ProjectLogType.EDIT, 'Edited'),
                    (ProjectLogType.COMPLETE, 'Completed'),
                )


class ProjectLog(models.Model):
    change_target = models.CharField(
        max_length=2,
        choices=ProjectLogSource.get_choices(),
        default=ProjectLogSource.TASK,
        blank=True,
        null=True,
    )
    change_type = models.CharField(
        max_length=2,
        choices=ProjectLogType.get_choices(),
        default=ProjectLogType.ADD,
        blank=True,
        null=True,
    )
    change_target_id = models.IntegerField(
        blank=True,
        null=True,
    )
    change_description = models.TextField(
        max_length=1000,
        blank=True,
        null=True,
    )
    change_date = models.DateTimeField(
        auto_now_add=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def is_type_add(self):
        return self.change_type == ProjectLogType.ADD

    def is_type_edit(self):
        return self.change_type == ProjectLogType.EDIT

    def is_type_remove(self):
        return self.change_type == ProjectLogType.REMOVE

    def is_type_complete(self):
        return self.change_type == ProjectLogType.COMPLETE

    def is_source_volunteer_application(self):
        return self.change_target == ProjectLogSource.VOLUNTEER_APPLICATION

    def is_source_volunteer(self):
        return self.change_target == ProjectLogSource.VOLUNTEER

    def is_source_task(self):
        return self.change_target == ProjectLogSource.TASK

    def is_source_task_review(self):
        return self.change_target == ProjectLogSource.TASK_REVIEW

    def is_source_staff(self):
        return self.change_target == ProjectLogSource.STAFF

    def is_source_status(self):
        return self.change_target == ProjectLogSource.STATUS

    def is_source_information(self):
        return self.change_target == ProjectLogSource.INFORMATION

    def is_source_scope(self):
        return self.change_target == ProjectLogSource.SCOPE

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
    DRAFT='DRF'
    NOT_STARTED='NOT'
    # ACCEPTING_VOLUNTEERS='AVL'
    STARTED='STA'
    WAITING_REVIEW='PRW'
    COMPLETED='COM'
    DELETED='DEL'

    def get_choices():
        return (
                    (TaskStatus.DRAFT, 'Draft'),
                    (TaskStatus.NOT_STARTED, 'Not started'),
                    # (TaskStatus.ACCEPTING_VOLUNTEERS, 'Accepting volunteers'),
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
    short_summary = models.TextField(
        verbose_name="Short summary",
        help_text="Write a short description of the task that will be used throughout the site when needing a compact description.",
        max_length=1000,
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

    def is_draft(self):
        return self.stage == TaskStatus.DRAFT

    def is_not_started(self):
        return self.stage == TaskStatus.NOT_STARTED

    def is_in_progress(self):
        return self.stage == TaskStatus.STARTED

    def is_pending_review(self):
        return self.stage == TaskStatus.WAITING_REVIEW

    def is_completed(self):
        return self.stage == TaskStatus.COMPLETED

    def is_type_scoping(self):
        return self.type == TaskType.SCOPING_TASK

    def is_type_project_management(self):
        return self.type == TaskType.PROJECT_MANAGEMENT_TASK

    def is_type_domain_work(self):
        return self.type == TaskType.DOMAIN_WORK_TASK

class ProjectDiscussionChannel(models.Model):
    name = models.TextField(
        max_length=100,
        verbose_name="Name",
        help_text="Descriptive name that identifies the discussion channel within the project.",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
    )
    related_task =  models.OneToOneField(
        ProjectTask,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    is_read_only =  models.BooleanField(
        verbose_name="Read only channel",
        help_text="Specifies if this channel has been archived and is read only.",
        default=False,
    )
    description = models.TextField(
        max_length=200,
        verbose_name="Description",
        help_text="Description of the purpose of this discussion channel.",
        blank=True,
        null=True,
    )

class ProjectComment(models.Model):
    comment = models.TextField(max_length=5000)
    comment_date = models.DateTimeField(auto_now_add=True)
    channel = models.ForeignKey(
        ProjectDiscussionChannel,
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.comment_date.strftime('%Y-%m-%d %H:%M') + self.author.username + ": " + self.comment[:100]

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
    public_reviewer_comments = models.TextField(
        verbose_name="Reviewer's comments",
        help_text="Add your feedback about the task. This is not private and will be shared with the volunteer.",
        max_length=2000,
        blank=True,
        null=True,
    )
    private_reviewer_notes = models.TextField(
        verbose_name="Private reviewer's notes",
        help_text="Private notes about the task. These notes will be shared with the rest of the project staff but not with the volunteer or anybody else.",
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
    review_score = models.PositiveSmallIntegerField(
        verbose_name="Score",
        help_text="What do you think about the quality of work in this task?",
        choices=Score.get_choices(),
        default=Score.ONE_STAR,
    )
    task = models.ForeignKey(
        ProjectTask,
        on_delete=models.CASCADE,
        verbose_name="Task",
        help_text="Project task this review is related to.",
    )
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Volunteer",
        help_text="The user requesting a review of this task.",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Review author",
        help_text="The user that did the QA review of this task.",
        related_name="reviewed_project_task",
        blank=True,
        null=True,
    )

    def is_pending(self):
        return self.review_result == ReviewStatus.NEW

    def is_accepted(self):
        return self.review_result == ReviewStatus.ACCEPTED

    def is_rejected(self):
        return self.review_result == ReviewStatus.REJECTED


class PinnedTaskReview(models.Model):
    task_review = models.ForeignKey(
        ProjectTaskReview,
        on_delete=models.CASCADE,
        verbose_name="Task review",
        help_text="Project task review this pinned review is holding.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Volunteer",
        help_text="The volunteer pinning the review.",
    )

    class Meta:
        unique_together = ('task_review','user')


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

    def is_level_beginner(self):
        return self.level == SkillLevel.BEGINNER

    def is_level_intermediate(self):
        return self.level == SkillLevel.INTERMEDIATE

    def is_level_expert(self):
        return self.level == SkillLevel.EXPERT

    def standard_display_name(self):
        return "{0}:{1} ({2})".format(self.skill.standard_display_name(), self.get_level_display(), self.get_importance_display())

    class Meta:
        unique_together = ('skill','task')


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
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Review author",
        help_text="The user that did the review of this volunteer application.",
        related_name="reviewed_volunteer_application",
        blank=True,
        null=True,
    )

    def is_new(self):
        return self.status == ReviewStatus.NEW

    def is_accepted(self):
        return self.status == ReviewStatus.ACCEPTED

    def is_rejected(self):
        return self.status == ReviewStatus.REJECTED

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
    SUPPORT_STAFF = 1

    def get_choices():
        return (
                    (TaskRole.VOLUNTEER, 'Volunteer'),
                    (TaskRole.SUPPORT_STAFF, 'Staff'),
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

    def __str__(self):
        return self.user.standard_display_name() + "-" + self.task.name + "-" + self.get_role_display()

    class Meta:
        unique_together = ('user', 'task', 'role')
