from django.db import IntegrityError, transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from datetime import date

from ..models.proj import (
    Project, ProjectStatus, ProjectRole, ProjRole, ProjectFollower, ProjectLog, ProjectLogType, ProjectLogSource, ProjectDiscussionChannel, ProjectComment,
    ProjectTask, TaskStatus, TaskRole, ProjectTaskRole, ProjectTaskReview, VolunteerApplication,
    ProjectTaskRequirement, TaskRequirementImportance, TaskType, ProjectScope, PinnedTaskReview,
    ProjectSocialCause,
)
from ..models.common import (
    ReviewStatus,
)
from ..models.user import (
    User, NotificationSeverity, NotificationSource, VolunteerProfile, Skill, BadgeTier, UserBadge, BadgeType,
)
from django.db.models import Case, When, Count, Q, Subquery, Avg, F

from .common import validate_consistent_keys, social_cause_view_model_translation, project_status_view_model_translation
from .notifications import NotificationService
from dssgmkt.authorization.common import ensure_user_has_permission

def filter_public_projects(query_set):
    return query_set.exclude(status=ProjectStatus.DRAFT) \
                    .exclude(status=ProjectStatus.EXPIRED) \
                    .exclude(status=ProjectStatus.DELETED)

class ProjectService():
    @staticmethod
    def get_project(request_user, projid):
        return Project.objects.filter(pk=projid).annotate(follower_count=Count('projectfollower')).first()

    @staticmethod
    def get_all_public_projects(request_user, search_config=None):
        # We could also add the projects that are non-public but that also belong
        # to the organizations that the user is member of. Should that be added
        # or should users access those projects through the page of their org?
        base_query = filter_public_projects(Project.objects.all())
        if search_config:
            if 'projname' in search_config:
                base_query = base_query.filter(name__icontains=search_config['projname'])
            if 'orgname' in search_config:
                base_query = base_query.filter(organization__name__icontains=search_config['orgname'])
            if 'skills' in search_config:
                for skill_fragment in search_config['skills'].split():
                    base_query = base_query.filter(projecttask__projecttaskrequirement__skill__name__icontains=skill_fragment.strip())
            if 'social_cause' in search_config:
                sc = search_config['social_cause']
                if isinstance(sc, str):
                    sc = [sc]
                social_causes = []
                for social_cause_from_view in sc:
                    social_causes.append(social_cause_view_model_translation[social_cause_from_view])
                # base_query = base_query.filter(project_cause__in=social_causes)
                base_query = base_query.filter(projectsocialcause__social_cause__in=social_causes).distinct()
            if 'project_status' in search_config:
                project_status_list = search_config['project_status']
                if isinstance(project_status_list, str):
                    project_status_list = [project_status_list]
                project_statuses = []
                for project_status_from_view in project_status_list:
                    status_filter = project_status_view_model_translation[project_status_from_view]
                    project_statuses.extend(status_filter)
                base_query = base_query.filter(status__in=project_statuses).distinct()
        return base_query.distinct().order_by('name')


    @staticmethod
    def get_all_organization_projects(request_user, org):
        return Project.objects.filter(organization=org).order_by('name')

    @staticmethod
    def get_featured_project():
        # Long-term, make a more intelligent selection, choosing for example
        # the project with best average task review score, the one with the
        # least deviation from estimates, etc.
        return filter_public_projects(
                Project.objects.all() \
                                .annotate(volunteercount=Count('projecttask__projecttaskrole'))) \
                                .order_by('-volunteercount').first()

    @staticmethod
    def get_organization_public_projects(request_user, org):
        return filter_public_projects(ProjectService.get_all_organization_projects(request_user, org))

    @staticmethod
    def user_is_project_owner(user, proj):
        return user.is_authenticated and ProjectRole.objects.filter(project=proj, user=user, role=ProjRole.OWNER).exists()

    @staticmethod
    def user_is_project_follower(user, proj):
        return user.is_authenticated and ProjectFollower.objects.filter(project=proj, user=user).exists()

    @staticmethod
    def user_is_project_volunteer(user, proj):
        return user.is_authenticated and ProjectTaskRole.objects.filter(user=user, role=TaskRole.VOLUNTEER, task__project=proj).exists()

    @staticmethod
    def user_is_volunteer(user):
        return ProjectTaskRole.objects.filter(user=user, role=TaskRole.VOLUNTEER, task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]).exists()

    @staticmethod
    def user_is_project_scoper(user, proj):
        return user.is_authenticated and ProjectTaskRole.objects.filter(user=user, role=TaskRole.VOLUNTEER, task__project=proj, task__type=TaskType.SCOPING_TASK, task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]).exists()

    @staticmethod
    def user_is_project_manager(user, proj):
        return user.is_authenticated and ProjectTaskRole.objects.filter(user=user, role=TaskRole.VOLUNTEER, task__project=proj, task__type=TaskType.PROJECT_MANAGEMENT_TASK, task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]).exists()

    @staticmethod
    def user_is_project_reviewer(user, proj):
        return user.is_authenticated and ProjectTaskRole.objects.filter(user=user, role=TaskRole.VOLUNTEER, task__project=proj, task__type=TaskType.QA_TASK, task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]).exists()

    @staticmethod
    def user_can_view_project_tasks(user, proj):
        return ProjectService.user_is_project_member(user, proj) or ProjectService.user_is_project_reviewer(user, proj)

    @staticmethod
    def user_can_review_project_tasks(user, proj):
        return ProjectService.user_is_project_owner(user, proj) or ProjectService.user_is_project_reviewer(user, proj)

    @staticmethod
    def user_can_complete_project(user, proj):
        return ProjectService.user_is_project_official(user, proj) # or ProjectService.user_is_project_reviewer(user, proj)

    @staticmethod
    def user_is_project_volunteer_official(user, proj):
        return user.is_authenticated and ProjectTaskRole.objects.filter(user=user, role=TaskRole.VOLUNTEER, task__project=proj, task__type__in=[TaskType.SCOPING_TASK, TaskType.PROJECT_MANAGEMENT_TASK], task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]).exists()

    @staticmethod
    def user_is_task_editor(user, proj):
        return ProjectService.user_is_project_owner(user, proj) or ProjectService.user_is_project_scoper(user, proj)

    @staticmethod
    def user_is_project_official(user, proj):
        return ProjectService.user_is_project_owner(user, proj) or ProjectService.user_is_project_volunteer_official(user, proj)

    @staticmethod
    def user_is_project_member(user, proj):
        return user.is_authenticated and (ProjectRole.objects.filter(project=proj, user=user).exists() or ProjectService.user_is_project_volunteer_official(user, proj))

    @staticmethod
    def user_is_project_commenter(user, proj):
        return user.is_authenticated and (ProjectService.user_is_project_member(user, proj) or ProjectService.user_is_project_volunteer(user, proj))

    @staticmethod
    def user_is_channel_commenter(user, channel):
        project = channel.project
        return user.is_authenticated and (ProjectService.user_is_project_member(user, project) or (not channel.related_task and ProjectService.user_is_project_volunteer(user, project)) or (channel.related_task and ProjectTaskService.user_is_task_volunteer(user, channel.related_task)))

    @staticmethod
    def is_project_visible_by_user(user, project):
        if project.status == ProjectStatus.DRAFT:
            # TODO Maybe add the project staff here.
            return ProjectService.user_is_project_owner(user, project)
        return True

    @staticmethod
    def get_project_officials(request_user, proj):
        return User.objects.filter(projectrole__project=proj, projectrole__role=ProjRole.OWNER).union(
            User.objects.filter(projecttaskrole__task__project=proj,
                                projecttaskrole__role=TaskRole.VOLUNTEER,
                                projecttaskrole__task__type__in=[TaskType.SCOPING_TASK, TaskType.PROJECT_MANAGEMENT_TASK],
                                projecttaskrole__task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]
                                )
        )

    @staticmethod
    def get_project_reviewers(request_user, proj):
        return User.objects.filter(projectrole__project=proj, projectrole__role=ProjRole.OWNER).union(
            User.objects.filter(projecttaskrole__task__project=proj,
                                projecttaskrole__role=TaskRole.VOLUNTEER,
                                projecttaskrole__task__type__in=[TaskType.QA_TASK],
                                projecttaskrole__task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]
                                )
        )

    @staticmethod
    def get_project_members(request_user, proj):
        return User.objects.filter(projectrole__project=proj).union(
            User.objects.filter(projecttaskrole__task__project=proj,
                                projecttaskrole__role=TaskRole.VOLUNTEER,
                                projecttaskrole__task__type__in=[TaskType.SCOPING_TASK, TaskType.PROJECT_MANAGEMENT_TASK],
                                projecttaskrole__task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]
                                )
        )

    @staticmethod
    def get_all_project_users(request_user, proj):
        return User.objects.filter(projectrole__project=proj).union(
            User.objects.filter(projecttaskrole__task__project=proj,
                                projecttaskrole__role=TaskRole.VOLUNTEER,
                                projecttaskrole__task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]
                                )
        )

    @staticmethod
    def get_public_notification_users(request_user, proj):
        return User.objects.filter(projectrole__project=proj).union(
            User.objects.filter(projecttaskrole__task__project=proj,
                                projecttaskrole__role=TaskRole.VOLUNTEER,
                                projecttaskrole__task__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW]
                                ).union(
                                    User.objects.filter(projectfollower__project=proj)
                                )
        ).distinct()

    @staticmethod
    def get_project_followers(request_user, proj):
        return User.objects.filter(projectfollower__project=proj)

    @staticmethod
    def get_project_changes(request_user, proj):
        ensure_user_has_permission(request_user, proj, 'project.log_view')
        return ProjectLog.objects.filter(project = proj).order_by('-change_date')

    @staticmethod
    def get_project_channels(request_user, proj):
        return ProjectDiscussionChannel.objects.filter(project=proj)

    @staticmethod
    def get_project_channel(request_user, proj, channelid):
        return ProjectDiscussionChannel.objects.get(pk=channelid, project=proj)

    @staticmethod
    def get_project_comments(request_user, channelid, proj):
        return ProjectComment.objects.filter(channel__id=channelid, channel__project=proj.id).order_by('-comment_date')

    @staticmethod
    def add_project_change(request_user, proj, type, target_type, target_id, description):
        change = ProjectLog()
        change.project = proj
        change.author = request_user
        change.change_type = type
        change.change_target = target_type
        change.change_target_id = target_id
        change.change_description = description
        change.save()

    @staticmethod
    def add_project_comment(request_user, projid, channelid, project_comment):
        project = Project.objects.get(pk=projid)
        if project:
            channel = ProjectService.get_project_channel(request_user, project, channelid)
            if not channel:
                raise KeyError('Discussion channel {0} not found'.format(channelid))
            ensure_user_has_permission(request_user, channel, 'project.comment_add')
            if channel.is_read_only:
                raise ValueError('Trying to post a comment on a read-only channel.')
            project_comment.author = request_user
            project_comment.channel = channel
            try:
                project_comment.save()
                NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                            "New comment added to the discussion channel {0} of project {1}.".format(channel.name, project.name),
                                                            NotificationSeverity.INFO,
                                                            NotificationSource.PROJECT,
                                                            project.id)
            except IntegrityError:
                raise ValueError('Cannot save comment')
        else:
            raise KeyError('Project not found ' + str(projid))

    @staticmethod
    def create_project(request_user, project, organization, organization_members):
        ensure_user_has_permission(request_user, organization, 'organization.project_create')
        with transaction.atomic():
            project.organization = organization
            project.status = ProjectStatus.DRAFT
            project.save()

            # Create default administrator
            project_admin_role = ProjectRole()
            project_admin_role.user = request_user
            project_admin_role.project = project
            project_admin_role.role = ProjRole.OWNER
            project_admin_role.save()

            # Create project scope
            project_scope = ProjectScope()
            project_scope.project = project
            project_scope.scope_goals = project.scope_goals
            project_scope.scope_interventions = project.scope_interventions
            project_scope.scope_available_data = project.scope_available_data
            project_scope.scope_analysis = project.scope_analysis
            project_scope.scope_validation_methodology = project.scope_validation_methodology
            project_scope.scope_implementation = project.scope_implementation
            project_scope.author = request_user
            project_scope.version_notes = "Initial scope at project creation time."
            project_scope.save()

            # Create default tasks
            scoping_task = ProjectTask()
            scoping_task.name = 'Project scoping'
            scoping_task.short_summary = 'Project scoping task to define the project work.'
            scoping_task.description = 'This project is new and needs help being defined. The project scoping includes defining the problem being solved, defining what form the soluntion will take, splitting the work into the necessary tasks, and specifying the expertise needed to complete each task. Project scopers will also review volunteer applications and will QA the work done by volunteers.'
            scoping_task.onboarding_instructions = 'Describe in detail the volunteer onboarding instructions for project scoping.'
            scoping_task.stage = TaskStatus.NOT_STARTED
            scoping_task.type = TaskType.SCOPING_TASK
            scoping_task.accepting_volunteers = False
            scoping_task.project = project
            scoping_task.percentage_complete = 0
            scoping_task.business_area = 'no'
            scoping_task.estimated_start_date = date.today()
            scoping_task.estimated_end_date = date.today()
            scoping_task.save()

            project_management_task = ProjectTask()
            project_management_task.name = 'Project management'
            project_management_task.short_summary = 'Project management task to ensure the project is successful.'
            project_management_task.description = 'This project needs experienced project managers that can ensure the project gets successfully completed on time. Duties include managing the status of all the tasks in the project, ensuring work gets done at the required pace, foreseeing risks to the project and preventing blockers. Project managers will also review volunteer applications and will QA the work done by volunteers.'
            project_management_task.onboarding_instructions = 'Describe in detail the volunteer onboarding instructions for project management.'
            project_management_task.stage = TaskStatus.DRAFT
            project_management_task.type = TaskType.PROJECT_MANAGEMENT_TASK
            project_management_task.accepting_volunteers = False
            project_management_task.project = project
            project_management_task.percentage_complete = 0
            project_management_task.business_area = 'no'
            project_management_task.estimated_start_date = date.today()
            project_management_task.estimated_end_date = date.today()
            project_management_task.save()

            domain_work_task = ProjectTask()
            domain_work_task.name = 'Example domain work task'
            domain_work_task.short_summary = 'Project work description.'
            domain_work_task.description = 'Domain work tasks represent the tasks that need to be completed to finish the project. '
            domain_work_task.onboarding_instructions = 'Describe in detail the volunteer onboarding instructions for this domain work task.'
            domain_work_task.stage = TaskStatus.DRAFT
            domain_work_task.type = TaskType.DOMAIN_WORK_TASK
            domain_work_task.accepting_volunteers = False
            domain_work_task.project = project
            domain_work_task.percentage_complete = 0
            domain_work_task.business_area = 'no'
            domain_work_task.estimated_start_date = date.today()
            domain_work_task.estimated_end_date = date.today()
            domain_work_task.save()

            qa_task = ProjectTask()
            qa_task.name = 'Task and project QA'
            qa_task.short_summary = 'Task for performing QA on the domain tasks.'
            qa_task.description = 'This project needs experienced volunteers to work on ensuring that the tasks that are completed by other volunteers meet the requirements and the expected levels of delivery quality. Duties include reviewing work that volunteers complete, giving constructive feedback, deciding when tasks are ready to be marked as completed, and reviewing the status of the project before the final signoff.'
            qa_task.onboarding_instructions = 'Describe in detail the volunteer onboarding instructions for this QA task.'
            qa_task.stage = TaskStatus.DRAFT
            qa_task.type = TaskType.QA_TASK
            qa_task.accepting_volunteers = False
            qa_task.project = project
            qa_task.percentage_complete = 0
            qa_task.business_area = 'no'
            qa_task.estimated_start_date = date.today()
            qa_task.estimated_end_date = date.today()
            qa_task.save()

            # Create default discussion channels
            general_channel = ProjectDiscussionChannel()
            general_channel.project = project
            general_channel.name = "General discussion"
            general_channel.description = "Discussion channel for general topics about the project."
            general_channel.save()

            technical_channel = ProjectDiscussionChannel()
            technical_channel.project = project
            technical_channel.name = "Technical talk"
            technical_channel.description = "Discussion channel for technical topics that are not specific to a single task."
            technical_channel.save()

            project_management_channel = ProjectDiscussionChannel()
            project_management_channel.project = project
            project_management_channel.name = "Project management"
            project_management_channel.related_task = project_management_task
            project_management_channel.description = "Discussion channel for the task Project management."
            project_management_channel.save()

            scoping_channel = ProjectDiscussionChannel()
            scoping_channel.project = project
            scoping_channel.name = "Project scoping"
            scoping_channel.related_task = scoping_task
            scoping_channel.description = "Discussion channel for the task Project scoping."
            scoping_channel.save()

            domain_work_channel = ProjectDiscussionChannel()
            domain_work_channel.project = project
            domain_work_channel.name = "Domain work"
            domain_work_channel.related_task = domain_work_task
            domain_work_channel.description = "Discussion channel for the task Domain work."
            domain_work_channel.save()

            qa_channel = ProjectDiscussionChannel()
            qa_channel.project = project
            qa_channel.name = "QA"
            qa_channel.related_task = qa_task
            qa_channel.description = "Discussion channel for the QA task."
            qa_channel.save()


            message = "The project {0} was created by {1} within the organization {2}.".format(project.name, request_user.standard_display_name(), organization.name)
            NotificationService.add_multiuser_notification(organization_members,
                                                     message,
                                                     NotificationSeverity.INFO,
                                                     NotificationSource.PROJECT,
                                                     project.id)
            NotificationService.add_user_notification(request_user,
                                                     "The project {0} was created successfully and you have been made project administrator. The next step is to define the project scope and to review the three default tasks that were created automatically.".format(project.name),
                                                     NotificationSeverity.INFO,
                                                     NotificationSource.PROJECT,
                                                     project.id)

            return project

    @staticmethod
    def save_project(request_user, projid, project):
        validate_consistent_keys(project, ('id', projid))
        ensure_user_has_permission(request_user, project, 'project.information_edit')
        project.save()
        message = "The project {0} was edited by {1}.".format(project.name, request_user.standard_display_name())
        NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                 message,
                                                 NotificationSeverity.INFO,
                                                 NotificationSource.PROJECT,
                                                 project.id)
        ProjectService.add_project_change(request_user,
                                           project,
                                           ProjectLogType.EDIT,
                                           ProjectLogSource.INFORMATION,
                                           project.id,
                                           message)

    @staticmethod
    def save_project_social_causes(request_user, projid, project, post_object):
        validate_consistent_keys(project, ('id', projid))
        ensure_user_has_permission(request_user, project, 'project.information_edit')
        social_causes = post_object.getlist('id_social_causes')
        with transaction.atomic():
            for sc in ProjectSocialCause.objects.filter(project=projid):
                sc.delete()
            for sc in social_causes:
                new_sc = ProjectSocialCause()
                new_sc.social_cause = sc
                new_sc.project = project
                new_sc.save()

    @staticmethod
    def publish_project(request_user, projid, project):
        validate_consistent_keys(project, ('id', projid))
        ensure_user_has_permission(request_user, project, 'project.publish')
        if project.status == ProjectStatus.DRAFT:
            # TODO ensure all the project description fields are filled out, or else raise an error
            project.status = ProjectStatus.NEW
            # When is the start date of a project? When it's published, when
            # volunteers start scoping the project, or when volunteers start
            # working on domain tasks?
            project.actual_start_date = timezone.now()
            project.save()
        message = "The project {0} was published by {1} and can now be applied to by volunteers.".format(project.name, request_user.standard_display_name())
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                 message,
                                                 NotificationSeverity.WARNING,
                                                 NotificationSource.PROJECT,
                                                 project.id)
        ProjectService.add_project_change(request_user,
                                           project,
                                           ProjectLogType.ADD,
                                           ProjectLogSource.STATUS,
                                           project.id,
                                           message)

    @staticmethod
    def finish_project(request_user, projid, project):
        validate_consistent_keys(project, ('id', projid))
        ensure_user_has_permission(request_user, project, 'project.approve_as_completed')
        if project.status == ProjectStatus.WAITING_REVIEW:
            project.status = ProjectStatus.COMPLETED
            project.actual_end_date = timezone.now()
            project.save()
        message = "The project {0} has been accepted as finished, so all the volunteer work has been completed.".format(project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                 message,
                                                 NotificationSeverity.INFO,
                                                 NotificationSource.PROJECT,
                                                 project.id)
        ProjectService.add_project_change(request_user,
                                           project,
                                           ProjectLogType.COMPLETE,
                                           ProjectLogSource.STATUS,
                                           project.id,
                                           message)

    @staticmethod
    def add_staff_member(request_user, projid, project_role):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.staff_edit')
        if project:
            project_role.project = project
            try:
                previous_members = ProjectService.get_project_members(request_user, project)
                project_role.save()
                message = "New staff member {0} added to the project {1} with role {2}.".format(project_role.user.standard_display_name(), project.name, project_role.get_role_display())
                NotificationService.add_multiuser_notification(previous_members,
                                                            message,
                                                            NotificationSeverity.INFO,
                                                            NotificationSource.PROJECT,
                                                            project.id)
                NotificationService.add_user_notification(project_role.user,
                                                            "You have been added as a member of project {0} with role {1}.".format(project.name, project_role.get_role_display()),
                                                            NotificationSeverity.INFO,
                                                            NotificationSource.PROJECT,
                                                            project.id)
                ProjectService.add_project_change(request_user,
                                                  project,
                                                  ProjectLogType.ADD,
                                                  ProjectLogSource.STAFF,
                                                  project_role.id,
                                                  message)
            except IntegrityError:
                raise ValueError('Duplicate user role')
        else:
            raise KeyError('Project not found ' + str(projid))

    @staticmethod
    def save_project_role(request_user, projid, project_role):
        validate_consistent_keys(project_role, 'Role does not match project', (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_role.project, 'project.staff_edit')
        current_role = ProjectService.get_project_role(project_role.user, projid,  project_role.id)
        if current_role.role == ProjRole.OWNER and \
            project_role.role != ProjRole.OWNER and \
            len(ProjectService.get_project_owners(request_user, projid)) <= 1:
            raise ValueError('You are trying to remove the last administrator of the project. Please appoint another administrator before removing the current one.')
        project_role.save()
        project = project_role.project
        message = "The role of {0} in project {1} has been changed to {2}.".format(project_role.user.standard_display_name(), project.name, project_role.get_role_display())
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                    message,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.PROJECT,
                                                    project.id)
        NotificationService.add_user_notification(project_role.user,
                                                    "Your role within project {0} has been changed to {1}.".format(project.name, project_role.get_role_display()),
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.PROJECT,
                                                    project.id)
        ProjectService.add_project_change(request_user,
                                          project,
                                          ProjectLogType.EDIT,
                                          ProjectLogSource.STAFF,
                                          project_role.id,
                                          message)

    @staticmethod
    def delete_project_role(request_user, projid, project_role):
        validate_consistent_keys(project_role, 'Role does not match project', (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_role.project, 'project.staff_remove')
        if project_role.role == ProjRole.OWNER and len(ProjectService.get_project_owners(request_user, projid)) <= 1:
            raise ValueError('You are trying to remove the last administrator of the project. Please appoint another administrator before removing the current one.')
        project_role.delete()
        project = project_role.project
        message = "The user {0} has been removed from the staff of project {1}.".format(project_role.user.standard_display_name(), project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                    message,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.PROJECT,
                                                    project.id)
        NotificationService.add_user_notification(project_role.user,
                                                    "You were removed from project {0} and are no longer part of its staff.".format(project.name),
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.PROJECT,
                                                    project.id)
        ProjectService.add_project_change(request_user,
                                          project,
                                          ProjectLogType.REMOVE,
                                          ProjectLogSource.STAFF,
                                          project_role.id,
                                          message)

    @staticmethod
    def get_all_project_scopes(request_user, projid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.scope_view')
        return ProjectScope.objects.filter(project=projid).order_by('-creation_date')

    @staticmethod
    def get_current_project_scope(request_user, projid):
        return ProjectService.get_all_project_scopes(request_user, projid).first()

    @staticmethod
    def get_project_scope(request_user, projid, scopeid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.scope_view')
        return ProjectScope.objects.get(pk=scopeid, project=projid)

    @staticmethod
    def update_project_scope(request_user, projid, project_scope):
        validate_consistent_keys(project_scope, (['project', 'id'], projid))
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.scope_edit')
        if project:
            if project.status in [ProjectStatus.COMPLETED, ProjectStatus.DELETED, ProjectStatus.EXPIRED]:
                raise ValueError('You cannot edit the scope of a completed project.')
            # We set the primary key of the project scope being "edited" so
            # Django inserts a new instance in the db.
            project_scope.id = None
            project_scope.creation_date = None
            try:
                project_scope.save()
                message = "The project scope of project {0} was edited by {1}.".format(project.name, request_user.standard_display_name())
                NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                            message,
                                                            NotificationSeverity.INFO,
                                                            NotificationSource.PROJECT,
                                                            project.id)
                ProjectService.add_project_change(request_user,
                                                  project,
                                                  ProjectLogType.EDIT,
                                                  ProjectLogSource.SCOPE,
                                                  project.id,
                                                  message)
            except IntegrityError:
                raise ValueError('Error saving project scope')
        else:
            raise KeyError('Project not found ' + str(projid))

    @staticmethod
    def get_all_project_staff(request_user, projid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.staff_view')
        return ProjectRole.objects.filter(project=projid).order_by('role')

    @staticmethod
    def get_project_owners(request_user, projid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.staff_view')
        return ProjectRole.objects.filter(project=projid, role=ProjRole.OWNER)

    @staticmethod
    def get_project_role(request_user, projid, roleid):
        return ProjectRole.objects.get(pk=roleid, project__id=projid)

    @staticmethod
    def get_all_project_volunteers(request_user, projid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.volunteers_view')
        return ProjectTaskRole.objects.filter(task__project__id=projid).order_by('-task__stage', 'user__first_name')

    @staticmethod
    def get_project_public_volunteer_list(request_user, projid):
        return User.objects.filter(projecttaskrole__task__project__id=projid).distinct()

    @staticmethod
    def get_all_volunteer_applications(request_user, projid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.volunteers_view')
        return VolunteerApplication.objects.filter(task__project__id = projid).order_by(
                        Case(When(status=ReviewStatus.NEW, then=0),
                             When(status=ReviewStatus.ACCEPTED, then=1),
                             When(status=ReviewStatus.REJECTED, then=1)), '-application_date')

    @staticmethod
    def toggle_follower(request_user, projid):
        if request_user.is_authenticated:
            project = Project.objects.get(pk=projid)
            if project:
                project_follower = ProjectFollower.objects.filter(project=project, user=request_user).first()
                if project_follower:
                    project_follower.delete()
                else:
                    project_follower = ProjectFollower()
                    project_follower.project = project
                    project_follower.user = request_user
                    project_follower.save()
            else:
                raise KeyError('Project not found')

    @staticmethod
    def get_user_projects_with_pending_volunteer_requests(request_user):
        return Project.objects.filter(projectrole__user=request_user,
                                      projectrole__role=ProjRole.OWNER,
                                      projecttask__volunteerapplication__status=ReviewStatus.NEW
                        ).union(Project.objects.filter(
                            projecttask__projecttaskrole__user=request_user,
                            projecttask__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW],
                            projecttask__type__in=[TaskType.SCOPING_TASK, TaskType.PROJECT_MANAGEMENT_TASK],
                            projecttask__volunteerapplication__status=ReviewStatus.NEW
                        )).distinct()

    @staticmethod
    def get_user_projects_with_pending_task_requests(request_user):
        if request_user.is_authenticated:
            return Project.objects.filter(projectrole__user=request_user,
                                          projectrole__role=ProjRole.OWNER,
                                          projecttask__projecttaskreview__review_result=ReviewStatus.NEW
                            ).union(Project.objects.filter(
                                        projecttask__projecttaskrole__user=request_user,
                                        projecttask__projecttaskrole__role=TaskRole.VOLUNTEER,
                                        projecttask__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW],
                                        projecttask__type__in=[TaskType.SCOPING_TASK, TaskType.PROJECT_MANAGEMENT_TASK],
                                    ).filter(
                                        projecttask__projecttaskreview__review_result=ReviewStatus.NEW,
                            )).distinct()
        else:
            return []

    @staticmethod
    def get_user_projects_in_draft_status(request_user):
        return Project.objects.filter(projectrole__user=request_user,
                                      projectrole__role=ProjRole.OWNER,
                                      status=ProjectStatus.DRAFT
                        ).distinct()

class ProjectTaskService():
    @staticmethod
    def get_project_task(request_user, projid, taskid):
        return ProjectTask.objects.get(pk=taskid, project=projid)

    @staticmethod
    def get_all_tasks(request_user, proj):
        ensure_user_has_permission(request_user, proj, 'project.tasks_view')
        return ProjectTask.objects.filter(project=proj).order_by('estimated_start_date')

    @staticmethod
    def get_open_tasks(request_user, proj):
        return ProjectTask.objects.filter(accepting_volunteers = True,
                                          project=proj).exclude(stage__in=[TaskStatus.COMPLETED, TaskStatus.DRAFT, TaskStatus.DELETED]).order_by('estimated_start_date')

    @staticmethod
    def get_public_tasks(request_user, proj):
        query_set = ProjectTask.objects.filter(project=proj) \
                                    .exclude(stage__in=[TaskStatus.DRAFT, TaskStatus.DELETED]) \
                                    .annotate(volunteer_count=Count('projecttaskrole', filter=Q(projecttaskrole__role=TaskRole.VOLUNTEER), distinct=True))
        if not request_user.is_anonymous:
            query_set = query_set.annotate(already_applied=Count('volunteerapplication', filter=Q(volunteerapplication__volunteer=request_user, volunteerapplication__status=ReviewStatus.NEW), distinct=True)) \
                                 .annotate(already_volunteer=Count('projecttaskrole', filter=Q(projecttaskrole__user=request_user, projecttaskrole__role=TaskRole.VOLUNTEER), distinct=True))
        return query_set.order_by( '-stage','-accepting_volunteers')

    @staticmethod
    def get_project_tasks_summary(request_user, proj):
        base_query = ProjectTask.objects.filter(project=proj) \
                                  .exclude(stage=TaskStatus.DELETED) \
                                  .order_by('-accepting_volunteers', '-stage')
        if ProjectService.user_is_project_reviewer(request_user, proj):
            base_query = base_query.filter(stage=TaskStatus.WAITING_REVIEW)
        return base_query

    @staticmethod
    def get_user_task_application_status(request_user, projid, taskid):
        return {'already_applied': VolunteerApplication.objects.filter(task=taskid, task__project=projid, volunteer=request_user, status=ReviewStatus.NEW).distinct().count() > 0,
                'already_volunteer': ProjectTaskRole.objects.filter(task=taskid, task__project=projid, user=request_user, role=TaskRole.VOLUNTEER).distinct().count() > 0}

    @staticmethod
    def get_open_project_tasks_summary(request_user, proj):
        query_set = ProjectTask.objects.filter(project=proj) \
                                .exclude(stage__in=[TaskStatus.DRAFT, TaskStatus.DELETED, TaskStatus.COMPLETED]) \
                                .exclude(accepting_volunteers=False)
        # if not request_user.is_anonymous:
        #     query_set = query_set.annotate(already_applied=Count('volunteerapplication', filter=Q(volunteerapplication__volunteer=request_user, volunteerapplication__status=ReviewStatus.NEW), distinct=True)) \
        #                          .annotate(already_volunteer=Count('projecttaskrole', filter=Q(projecttaskrole__user=request_user, projecttaskrole__role=TaskRole.VOLUNTEER), distinct=True))
        return query_set.order_by('estimated_start_date')

    @staticmethod
    def get_non_finished_tasks(request_user, proj):
        return ProjectTask.objects.filter(project=proj).exclude(stage__in=[TaskStatus.DRAFT, TaskStatus.COMPLETED, TaskStatus.DELETED]).order_by('estimated_start_date')

    @staticmethod
    def get_volunteer_current_tasks(request_user, volunteer, projid):
        ensure_user_has_permission(request_user, volunteer, 'user.is_same_user')
        return ProjectTask.objects.filter(project__pk=projid,
                                          projecttaskrole__user=volunteer,
                                          stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW])

    @staticmethod
    def get_volunteer_open_task_applications(request_user, projid):
        base_query = VolunteerApplication.objects.filter(status=ReviewStatus.NEW, volunteer=request_user)
        if projid:
            base_query = base_query.filter(task__project=projid)
        return base_query

    @staticmethod
    def get_volunteer_all_tasks(request_user, target_user):
        return ProjectTask.objects.filter(projecttaskrole__user=target_user).exclude(project__status=ProjectStatus.DRAFT).order_by('-stage')

    @staticmethod
    def get_volunteer_all_project_tasks(request_user, target_user, project):
        return ProjectTask.objects.filter(projecttaskrole__user=target_user, projecttaskrole__role=TaskRole.VOLUNTEER, project=project)

    @staticmethod
    def user_is_task_volunteer(user, task):
        return user.is_authenticated and ProjectTaskRole.objects.filter(user=user, role=TaskRole.VOLUNTEER, task=task).exists()

    @staticmethod
    def user_can_view_task_review(user, task_review):
        return user.is_authenticated and (ProjectService.user_is_project_member(user, task_review.task.project) or ProjectTaskService.user_belongs_to_task_review(user, task_review) or ProjectService.user_is_project_reviewer(user, task_review.task.project))

    @staticmethod
    def user_can_view_all_task_reviews(user, task):
        return user.is_authenticated and (ProjectService.user_is_project_member(user, task.project) or ProjectTaskService.user_is_task_volunteer(user, task))

    @staticmethod
    def user_can_view_volunteer_application(user, volunteer_application):
        return user == volunteer_application.volunteer or ProjectService.user_is_project_official(user, volunteer_application.task.project)

    @staticmethod
    def user_can_review_task(user, task):
        return ProjectService.user_can_review_project_tasks(user, task.project) and not ProjectTaskRole.objects.filter(user=user, task=task).exists()

    @staticmethod
    def task_has_volunteers(request_user, taskid):
        return ProjectTaskRole.objects.filter(task=taskid, role=TaskRole.VOLUNTEER).exists()

    @staticmethod
    def get_task_volunteers(request_user, taskid):
        return User.objects.filter(projecttaskrole__task=taskid, projecttaskrole__role=TaskRole.VOLUNTEER)

    @staticmethod
    def get_task_staff(request_user, taskid):
        return User.objects.filter(projecttaskrole__task=taskid, projecttaskrole__role=TaskRole.SUPPORT_STAFF)


    @staticmethod
    def save_task_internal(request_user, projid, taskid, project_task):
        # The notifications are inside the transaction block and that is not ideal,
        # but the logic is not trivial and there is no obvious way to separate
        # them from the project/task db modifications.
        with transaction.atomic():
            current_task = ProjectTask.objects.get(pk=project_task.id)
            project_task.save()
            if project_task.name != current_task.name and project_task.projectdiscussionchannel:
                channel = project_task.projectdiscussionchannel
                channel.name = project_task.name
                channel.description = "Discussion channel for the project task {0}".format(project_task.name)
                channel.save()
            project = project_task.project
            if project_task.stage != current_task.stage:
                if project_task.type == TaskType.SCOPING_TASK:
                    if project_task.stage == TaskStatus.COMPLETED:
                        if project.status == ProjectStatus.WAITING_DESIGN_APPROVAL:
                            # Open to volunteers all the defined tasks of the project
                            domain_tasks = ProjectTask.objects.filter(project=project, type=TaskType.DOMAIN_WORK_TASK, stage=TaskStatus.NOT_STARTED)
                            for t in domain_tasks:
                                t.accepting_volunteers = True
                                t.save()
                            # Move the project to status waiting staff
                            project.status = ProjectStatus.WAITING_STAFF
                            project.save()
                            message = "The status of project {0} has changed to 'Staffing', so users can now apply to volunteer in the project tasks.".format(project.name)
                            NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                                     message,
                                                                     NotificationSeverity.INFO,
                                                                     NotificationSource.PROJECT,
                                                                     project.id)
                            ProjectService.add_project_change(request_user,
                                                               project,
                                                               ProjectLogType.EDIT,
                                                               ProjectLogSource.STATUS,
                                                               project.id,
                                                               message)
                    elif project_task.stage == TaskStatus.WAITING_REVIEW:
                        if project.status == ProjectStatus.DESIGN:
                            # Move the project to status waiting design review
                            project.status = ProjectStatus.WAITING_DESIGN_APPROVAL
                            project.save()
                            message = "The status of project {0} has changed to 'Scoping QA'; the project's staff will review the current scope and determine if it is final and thus the project work can begin, or if the current scope needs further modifications.".format(project.name)
                            NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                                     message,
                                                                     NotificationSeverity.INFO,
                                                                     NotificationSource.PROJECT,
                                                                     project.id)
                            ProjectService.add_project_change(request_user,
                                                               project,
                                                               ProjectLogType.EDIT,
                                                               ProjectLogSource.STATUS,
                                                               project.id,
                                                               message)
                elif project_task.type == TaskType.PROJECT_MANAGEMENT_TASK:
                    pass
                else:
                    if project_task.stage == TaskStatus.COMPLETED:
                        # Check that there are no more open tasks, then move the project to waiting review stage
                        with_open_tasks = ProjectTask.objects.filter(project=project).exclude(stage=TaskStatus.COMPLETED).exists()
                        if not with_open_tasks:
                            project.status = ProjectStatus.WAITING_REVIEW
                            project.save()
                            message = "The status of project {0} has changed to 'Final QA'; the project's work has finished and the staff will now verify if the project can be considered finished or if additional work needs to be completed.".format(project.name)
                            NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                                     message,
                                                                     NotificationSeverity.INFO,
                                                                     NotificationSource.PROJECT,
                                                                     project.id)
                            ProjectService.add_project_change(request_user,
                                                               project,
                                                               ProjectLogType.EDIT,
                                                               ProjectLogSource.STATUS,
                                                               project.id,
                                                               message)
                        elif not ProjectTask.objects.filter(project=project, type=TaskType.DOMAIN_WORK_TASK).exclude(stage=TaskStatus.COMPLETED).exists():
                            message = "The last domain work task of project {0} has been finished, but there are still other tasks (non-domain work) open.".format(project.name)
                            NotificationService.add_multiuser_notification(ProjectService.get_project_officials(request_user, project),
                                                                     message,
                                                                     NotificationSeverity.WARNING,
                                                                     NotificationSource.PROJECT,
                                                                     project.id)



    @staticmethod
    def save_task(request_user, projid, taskid, project_task):
        validate_consistent_keys(project_task, 'Task not found in that project', ('id', taskid), (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task.project, 'project.task_edit')
        # We have to get the task status saved in the DB, not the status that
        # comes from the editing form, as the user could be changing the task
        # status to completed.
        if ProjectTaskService.get_project_task(request_user, projid, taskid).stage == TaskStatus.COMPLETED:
            raise ValueError('Cannot edit a completed task')
        ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)
        project = project_task.project
        message = "The task {0} from project {1} has been edited.".format(project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                     message,
                                                     NotificationSeverity.INFO,
                                                     NotificationSource.TASK,
                                                     project_task.id)
        ProjectService.add_project_change(request_user,
                                       project,
                                       ProjectLogType.EDIT,
                                       ProjectLogSource.TASK,
                                       project_task.id,
                                       message)

    @staticmethod
    def mark_task_as_completed(request_user, projid, taskid, project_task_review):
        project_task = ProjectTask.objects.get(pk=taskid, project__id=projid)
        project = Project.objects.get(pk=projid)
        if project and project_task:
            ensure_user_has_permission(request_user, project_task, 'project.volunteer_task_finish')
            if not project_task.stage == TaskStatus.STARTED:
                raise ValueError('Cannot mark a task as completed if it is not in started state')
            # TODO if the task is a scoping task, verify that all the fields in the project scope are filled out, or else raise an error
            with transaction.atomic():
                project_task_review.task = project_task
                project_task_review.volunteer = request_user
                project_task_review.review_result = ReviewStatus.NEW
                project_task_review.save()
                project_task.stage = TaskStatus.WAITING_REVIEW
                ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)
            message = "The task {0} from project {1} has been marked as completed by the volunteer and needs to be reviewed.".format(project_task.name, project.name)
            NotificationService.add_multiuser_notification(ProjectService.get_project_reviewers(request_user, project),
                                                        message,
                                                        NotificationSeverity.WARNING,
                                                        NotificationSource.TASK,
                                                        project_task.id)
            NotificationService.add_multiuser_notification(ProjectTaskService.get_task_volunteers(request_user, taskid),
                                                        "Your task {0} of project {1} is now marked as finished. The project staff will review it and you will be notified when the QA is finished.".format(project_task.name, project.name),
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.TASK,
                                                        project_task.id)
            ProjectService.add_project_change(request_user,
                                            project,
                                            ProjectLogType.COMPLETE,
                                            ProjectLogSource.TASK,
                                            project_task.id,
                                            message)
        else:
            if not project:
                raise KeyError('Project not found ' + str(projid))
            else:
                raise KeyError('Task not found ' + str(taskid))

    @staticmethod
    def delete_task(request_user, projid, project_task):
        validate_consistent_keys(project_task, 'Task not found in that project', (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task.project, 'project.task_delete')
        if project_task.stage == TaskStatus.COMPLETED:
            raise ValueError('Cannot delete a completed task')
        if ProjectTaskService.task_has_volunteers(request_user, project_task.id):
            raise ValueError('Cannot delete a task with active volunteers. Remove them or assign them to a different task before deleting this task.')
        if project_task.projectdiscussionchannel:
            if project_task.stage == TaskStatus.NOT_STARTED:
                project_task.projectdiscussionchannel.delete()
            else:
                channel = project_task.projectdiscussionchannel
                channel.related_task = None
                channel.is_read_only = True
                channel.save()
        project_task.delete()
        project = project_task.project
        message = "The task {0} has been deleted from project {1}.".format(project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                     message,
                                                     NotificationSeverity.WARNING,
                                                     NotificationSource.TASK,
                                                     project_task.id)
        ProjectService.add_project_change(request_user,
                                           project,
                                           ProjectLogType.REMOVE,
                                           ProjectLogSource.TASK,
                                           project_task.id,
                                           message)

    @staticmethod
    def create_default_task(request_user, projid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.task_edit')
        if project:
            project_task = ProjectTask()
            project_task.name = 'New project task'
            project_task.short_summary = 'This is the task short summary'
            project_task.description = 'This is the task description'
            project_task.onboarding_instructions = 'These are the volunteer onboarding instructions'
            project_task.stage = TaskStatus.DRAFT
            project_task.accepting_volunteers = False
            project_task.project = project
            project_task.percentage_complete = 0
            project_task.business_area = 'no'
            project_task.estimated_start_date = date.today()
            project_task.estimated_end_date = date.today()
            project_task.save()

            channel = ProjectDiscussionChannel()
            channel.name = project_task.name
            channel.description = "Discussion channel for the project task {0}".format(project_task.name)
            channel.related_task = project_task
            channel.project = project
            channel.save()

            if project.status == ProjectStatus.WAITING_REVIEW:
                project.status = ProjectStatus.IN_PROGRESS
                project.save()
                message = "The status of project {0} has changed to 'In progress' as the staff determined that the project was not ready to be marked as finished.".format(project.name)
                NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                         message,
                                                         NotificationSeverity.INFO,
                                                         NotificationSource.PROJECT,
                                                         project.id)
                ProjectService.add_project_change(request_user,
                                                   project,
                                                   ProjectLogType.EDIT,
                                                   ProjectLogSource.STATUS,
                                                   project.id,
                                                   message)
            message = "A new task {0} has been added to project {1}.".format(project_task.name, project.name)
            NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                     message,
                                                     NotificationSeverity.WARNING,
                                                     NotificationSource.TASK,
                                                     project_task.id)
            ProjectService.add_project_change(request_user,
                                               project,
                                               ProjectLogType.ADD,
                                               ProjectLogSource.TASK,
                                               project_task.id,
                                               message)
            return project_task
        else:
            raise KeyError('Project not found')

    @staticmethod
    def get_project_task_review(request_user, projid, taskid, reviewid):
        project = Project.objects.get(pk=projid)
        task_review = ProjectTaskReview.objects.get(pk=reviewid)
        ensure_user_has_permission(request_user, task_review, 'project.task_review_view')
        validate_consistent_keys(task_review, 'Task review not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        return task_review

    @staticmethod
    def save_task_review(request_user, projid, taskid, task_review):
        validate_consistent_keys(task_review, 'Task review not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        project_task = ProjectTask.objects.get(pk=taskid)
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project_task.project, 'project.task_review_do')
        with transaction.atomic():
            # Tasks are allowed to have multiple volunteers. Any of them can
            # mark the task as finished, and a successful QA review will apply
            # to all of them.
            task_review.save()
            if task_review.review_result == ReviewStatus.ACCEPTED:
                project_task.stage = TaskStatus.COMPLETED
                project_task.accepting_volunteers = False
                project_task.percentage_complete = 1.0
                project_task.actual_effort_hours = task_review.volunteer_effort_hours
                project_task.actual_end_date = timezone.now()
                ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)
                for role in project_task.projecttaskrole_set.all():
                    ProjectTaskService.update_user_task_count(role.user)
                    ProjectTaskService.update_user_review_score(role.user)
                    ProjectTaskService.update_user_work_speed(role.user)
            elif task_review.review_result == ReviewStatus.REJECTED and project_task.stage != TaskStatus.COMPLETED:
                project_task.stage = TaskStatus.STARTED
                ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)
                for role in project_task.projecttaskrole_set.all():
                    ProjectTaskService.update_user_review_score(role.user)


    @staticmethod
    def update_user_badge(request_user, badge_type, badge_tier, badge_name):
        if badge_tier is not None:
            try:
                current_badge = UserBadge.objects.get(user=request_user, type=badge_type)
                if current_badge.tier != badge_tier:
                    is_better_badge = current_badge.tier < badge_tier
                    current_badge.tier = badge_tier
                    current_badge.save()
                    if is_better_badge:
                        message = "Congratulations! Your award for {0} has increased to {1}. Keep up with the good work!".format(badge_name, current_badge.get_tier_display())
                    else:
                        message = "Unfortunately your award for {0} has decreased to {1}.".format(badge_name, current_badge.get_tier_display())
                    NotificationService.add_user_notification(request_user,
                                                             message,
                                                             NotificationSeverity.INFO,
                                                             NotificationSource.BADGE,
                                                             current_badge.id)
            except:
                new_badge = UserBadge()
                new_badge.type = badge_type
                new_badge.tier = badge_tier
                new_badge.user = request_user
                new_badge.save()
                message = "Congratulations! You have been awarded a new badge ({0}) for {1}. Keep up with the good work!".format(new_badge.get_tier_display(), badge_name)
                NotificationService.add_user_notification(request_user,
                                                         message,
                                                         NotificationSeverity.INFO,
                                                         NotificationSource.BADGE,
                                                         new_badge.id)
        else:
            try:
                current_badge = UserBadge.objects.get(user=request_user, type=badge_type)
                current_badge.delete()
                message = "Unfortunately your award for {0} was removed.".format(badge_name, current_badge.get_tier_display())
                NotificationService.add_user_notification(request_user,
                                                         message,
                                                         NotificationSeverity.INFO,
                                                         NotificationSource.BADGE,
                                                         current_badge.id)
            except:
                pass


    @staticmethod
    def update_user_task_count(request_user):
        try:
            completed_task_count = ProjectTaskRole.objects.filter(task__stage=TaskStatus.COMPLETED, user=request_user).count()
            try:
                request_user.volunteerprofile.completed_task_count = completed_task_count
                request_user.volunteerprofile.save()
            except:
                pass
            badge_tier = None
            if completed_task_count > 10:
                badge_tier = BadgeTier.MASTER
            elif completed_task_count > 5:
                badge_tier = BadgeTier.ADVANCED
            elif completed_task_count > 0:
                badge_tier = BadgeTier.BASIC
            ProjectTaskService.update_user_badge(request_user, BadgeType.NUMBER_OF_PROJECTS, badge_tier, "completing tasks")
        except:
            pass # TODO log this exception


    @staticmethod
    def update_user_review_score(request_user):
        try:
            average_review_score = ProjectTaskReview.objects.filter(volunteer=request_user, review_result=ReviewStatus.ACCEPTED).aggregate(Avg('review_score'))['review_score__avg']
            if average_review_score is not None:
                try:
                    request_user.volunteerprofile.average_review_score = average_review_score
                    request_user.volunteerprofile.save()
                except:
                    pass
                badge_tier = None
                if average_review_score >= 4:
                    badge_tier = BadgeTier.MASTER
                elif average_review_score >= 3:
                    badge_tier = BadgeTier.ADVANCED
                elif average_review_score >= 2:
                    badge_tier = BadgeTier.BASIC
                ProjectTaskService.update_user_badge(request_user, BadgeType.REVIEW_SCORE, badge_tier, "getting great reviews")
        except:
            pass # TODO log this exception


    @staticmethod
    def update_user_work_speed(request_user):
        try:
            completed_tasks = ProjectTaskRole.objects.filter(task__stage=TaskStatus.COMPLETED, user=request_user)
            completed_task_count = completed_tasks.count()

            if completed_task_count > 0:
                # TODO make this query work instead of iterating over all the tasks
                # ahead_of_time_count = ProjectTaskRole.objects.filter(task__stage=TaskStatus.COMPLETED, user=request_user, \
                #                             task__actual_end_date__lt=F('task__estimated_end_date') - F('task__estimated_start_date') + F('task__actual_start_date')).count()
                ahead_of_time_count = 0
                for task_role in completed_tasks.all():
                    task = task_role.task
                    if task and task.estimated_end_date is not None and task.estimated_start_date is not None \
                        and task.actual_end_date is not None and task.actual_start_date is not None:
                        if task.estimated_end_date - task.estimated_start_date > task.actual_end_date - task.actual_start_date:
                            ahead_of_time_count += 1

                percentage_fast = float(ahead_of_time_count) / float(completed_task_count)
                try:
                    request_user.volunteerprofile.ahead_of_time_task_ratio = percentage_fast
                    request_user.volunteerprofile.save()
                except:
                    pass
                badge_tier = None
                if percentage_fast >= 0.85:
                    badge_tier = BadgeTier.MASTER
                elif percentage_fast >= 0.75:
                    badge_tier = BadgeTier.ADVANCED
                elif percentage_fast >= 0.5:
                    badge_tier = BadgeTier.BASIC
                ProjectTaskService.update_user_badge(request_user, BadgeType.WORK_SPEED, badge_tier, "being ahead of schedule")
        except:
            pass # TODO log this exception


    @staticmethod
    def accept_task_review(request_user, projid, taskid, task_review):
        validate_consistent_keys(task_review, 'Task review not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        ensure_user_has_permission(request_user, task_review.task.project, 'project.task_review_do')
        if task_review.review_result != ReviewStatus.NEW:
            raise ValueError('Task review was already completed')
        task_review.review_result = ReviewStatus.ACCEPTED
        task_review.reviewer = request_user
        task_review.review_date = timezone.now()
        ProjectTaskService.save_task_review(request_user, projid, taskid, task_review)
        project_task = task_review.task
        project = project_task.project
        message = "The task {0} from project {1} has been accepted during its QA phase and it's now completed.".format(project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                    message,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.TASK,
                                                    project_task.id)
        NotificationService.add_multiuser_notification(ProjectTaskService.get_task_volunteers(request_user, project_task.id),
                                                    "Congratulations! Your task {0} of project {1} has been reviewed by the project staff and accepted as finished, so your work has been completed. The staff comments are: {2}.".format(project_task.name, project.name, task_review.public_reviewer_comments),
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.TASK,
                                                    project_task.id)
        ProjectService.add_project_change(request_user,
                                          project,
                                          ProjectLogType.COMPLETE,
                                          ProjectLogSource.TASK_REVIEW,
                                          task_review.id,
                                          message)

    @staticmethod
    def reject_task_review(request_user, projid, taskid, task_review):
        validate_consistent_keys(task_review, 'Task review not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        ensure_user_has_permission(request_user, task_review.task.project, 'project.task_review_do')
        if task_review.review_result != ReviewStatus.NEW:
            raise ValueError('Task review was already completed')
        task_review.review_result = ReviewStatus.REJECTED
        task_review.reviewer = request_user
        task_review.review_date = timezone.now()
        ProjectTaskService.save_task_review(request_user, projid, taskid, task_review)
        project_task = task_review.task
        project = project_task.project
        message = "The task {0} from project {1} has been rejected during QA phase.".format(project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                    message,
                                                    NotificationSeverity.WARNING,
                                                    NotificationSource.TASK,
                                                    project_task.id)
        NotificationService.add_user_notification(task_review.volunteer,
                                                    "Your task {0} of project {1} has been reviewed by the project staff and rejected as finished, so it has been reopened. The staff comments are: {2}.".format(project_task.name, project.name, task_review.public_reviewer_comments),
                                                    NotificationSeverity.ERROR,
                                                    NotificationSource.TASK,
                                                    project_task.id)
        ProjectService.add_project_change(request_user,
                                          project,
                                          ProjectLogType.REMOVE,
                                          ProjectLogSource.TASK_REVIEW,
                                          task_review.id,
                                          message)
        if project_task.type == TaskType.SCOPING_TASK:
            if project.status == ProjectStatus.WAITING_DESIGN_APPROVAL:
                # Move project to status scoping
                project.status = ProjectStatus.DESIGN
                project.save()
                message = "The status of project {0} has changed to 'Scoping' as the project's staff determined that the scope needs modifications.".format(project.name)
                NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                         message,
                                                         NotificationSeverity.INFO,
                                                         NotificationSource.PROJECT,
                                                         project.id)
                ProjectService.add_project_change(request_user,
                                                   project,
                                                   ProjectLogType.EDIT,
                                                   ProjectLogSource.STATUS,
                                                   project.id,
                                                   message)

    @staticmethod
    def cancel_volunteering(request_user, projid, taskid, project_task_role):
        validate_consistent_keys(project_task_role, 'Task role not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task_role.task, 'project.volunteer_task_cancel')
        if project_task_role.user != request_user:
            raise ValueError('Role does not match current user')
        elif project_task_role.task.stage in [TaskStatus.DRAFT, TaskStatus.NOT_STARTED, TaskStatus.COMPLETED]:
            raise ValueError('Only tasks in progress and/or QA can be cancelled by the volunteer')
        else:
            project_task = project_task_role.task
            with transaction.atomic():
                project_task_role.delete()
                if not ProjectTaskService.task_has_volunteers(request_user, taskid):
                    project_task.stage = TaskStatus.STARTED ## or not started?
                    project_task.accepting_volunteers = True
                    ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)
            project = project_task.project
            message = "The volunteer {0} working on task {1} of project {2} has canceled the work and has stopped volunteering in the project.".format(project_task_role.user.standard_display_name(), project_task.name, project.name)
            NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                        message,
                                                        NotificationSeverity.ERROR,
                                                        NotificationSource.TASK,
                                                        project_task.id)
            NotificationService.add_user_notification(project_task_role.user,
                                                        "You have stopped working on task {0} of project {1}.".format(project_task.name, project.name),
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.TASK,
                                                        project_task.id)
            ProjectService.add_project_change(request_user,
                                              project,
                                              ProjectLogType.REMOVE,
                                              ProjectLogSource.VOLUNTEER,
                                              project_task_role.id,
                                              message)


    @staticmethod
    def apply_to_volunteer(request_user, projid, taskid, task_application_request):
        # TODO check that the task is not in draft stage
        # TODO check that the user does not have a NEW status application already
        project_task = ProjectTask.objects.get(pk=taskid, project__id=projid)
        validate_consistent_keys(project_task, 'Task not found in that project', (['project', 'id'], projid))
        ensure_user_has_permission(request_user, None, 'project.task_apply')
        if ProjectTaskService.user_is_task_volunteer(request_user, project_task):
            raise ValueError('User is already a volunteer of this task')
        # TODO remove this check because it is checked by the permissions of the method
        if not VolunteerProfile.objects.filter(user=request_user).exists(): # We cannot call UserService.user_has_volunteer_profile because a circular dependency # TODO split userService and ProjectService in two services each, one for queries, one for operations
            raise ValueError('User is not a volunteer')
        task_application_request.status = ReviewStatus.NEW
        task_application_request.task = project_task
        task_application_request.volunteer = request_user
        task_application_request.save()
        project = project_task.project
        message = "User {0} has applied to volunteer on task {1} of project {2}. Please review the application and accept or reject it as soon as possible.".format(task_application_request.volunteer.standard_display_name(), project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_officials(request_user, project),
                                                    message,
                                                    NotificationSeverity.WARNING,
                                                    NotificationSource.VOLUNTEER_APPLICATION,
                                                    task_application_request.id)
        NotificationService.add_user_notification(task_application_request.volunteer,
                                                    "You have applied to volunteer on task {0} of project {1}. The project staff will review the application and notify you of their decision as soon as possible.".format(project_task.name, project.name),
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.VOLUNTEER_APPLICATION,
                                                    task_application_request.id)
        ProjectService.add_project_change(request_user,
                                          project,
                                          ProjectLogType.ADD,
                                          ProjectLogSource.VOLUNTEER_APPLICATION,
                                          task_application_request.id,
                                          message)

    @staticmethod
    def get_volunteer_application(request_user, projid, taskid, volunteer_application_pk):
        # We can avoid doing this by using all the constraints in the DB query
        # volunteer_application = VolunteerApplication.objects.get(pk=volunteer_application_pk)
        # validate_consistent_keys(volunteer_application, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        # like so:
        volunteer_application = VolunteerApplication.objects.get(pk=volunteer_application_pk, task__id=taskid, task__project__id=projid)
        ensure_user_has_permission(request_user, volunteer_application, 'project.volunteers_application_view')
        return volunteer_application

    @staticmethod
    def save_volunteer_application(request_user, projid, taskid, volunteer_application):
        validate_consistent_keys(volunteer_application, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        project_task = ProjectTask.objects.get(pk=taskid)
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.volunteers_application_review')
        with transaction.atomic():
            if not volunteer_application.is_new():
                volunteer_application.resolution_date = timezone.now()
            volunteer_application.save()
            if volunteer_application.status == ReviewStatus.ACCEPTED:
                task_role = ProjectTaskRole()
                task_role.role = TaskRole.VOLUNTEER
                task_role.task = project_task
                task_role.user = volunteer_application.volunteer
                task_role.save()
                if project_task.stage == TaskStatus.NOT_STARTED:
                    project_task.stage = TaskStatus.STARTED
                    project_task.actual_start_date = timezone.now()
                    project_task.save()
                if project.status == ProjectStatus.NEW:
                    if project_task.type == TaskType.SCOPING_TASK:
                        # Move project to status scoping
                        project.status = ProjectStatus.DESIGN
                        project.save()
                        message = "The status of project {0} has changed to 'Scoping', as new volunteers have been accepted to work on the project scope.".format(project.name)
                        NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                                 message,
                                                                 NotificationSeverity.INFO,
                                                                 NotificationSource.PROJECT,
                                                                 project.id)
                        ProjectService.add_project_change(request_user,
                                                           project,
                                                           ProjectLogType.EDIT,
                                                           ProjectLogSource.STATUS,
                                                           project.id,
                                                           message)
                elif project.status == ProjectStatus.WAITING_STAFF:
                    if project_task.type == TaskType.DOMAIN_WORK_TASK:
                        # Move project to status in progress
                        project.status = ProjectStatus.IN_PROGRESS
                        project.save()
                        message = "The status of project {0} has changed to 'In progress', as volunteers have been accepted to work on the project tasks.".format(project.name)
                        NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                                 message,
                                                                 NotificationSeverity.INFO,
                                                                 NotificationSource.PROJECT,
                                                                 project.id)
                        ProjectService.add_project_change(request_user,
                                                           project,
                                                           ProjectLogType.EDIT,
                                                           ProjectLogSource.STATUS,
                                                           project.id,
                                                           message)

    @staticmethod
    def accept_volunteer(request_user, projid, taskid, volunteer_application):
        validate_consistent_keys(volunteer_application, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        if request_user.is_anonymous:
            raise PermissionDenied()
        if volunteer_application.status != ReviewStatus.NEW:
            raise ValueError('Volunteer application review was already completed')
        volunteer_application.status = ReviewStatus.ACCEPTED
        volunteer_application.reviewer = request_user
        volunteer_application.review_date = timezone.now()
        ProjectTaskService.save_volunteer_application(request_user, projid, taskid, volunteer_application)
        project_task = volunteer_application.task
        project = project_task.project
        message = "The user {0} has been accepted as volunteer for task {1} of project {2}.".format(volunteer_application.volunteer.standard_display_name(), project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                    message,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.VOLUNTEER_APPLICATION,
                                                    volunteer_application.id)
        NotificationService.add_user_notification(volunteer_application.volunteer,
                                                    "Congratulations! Your volunteer application for task {0} of project {1} has been accepted! You can now start working on this project. The reviewer's comments are: {2}".format(project_task.name, project.name, volunteer_application.public_reviewer_comments),
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.VOLUNTEER_APPLICATION,
                                                    volunteer_application.id)
        ProjectService.add_project_change(request_user,
                                          project,
                                          ProjectLogType.COMPLETE,
                                          ProjectLogSource.VOLUNTEER_APPLICATION,
                                          volunteer_application.id,
                                          message)

    @staticmethod
    def reject_volunteer(request_user, projid, taskid, volunteer_application):
        validate_consistent_keys(volunteer_application, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        if request_user.is_anonymous:
            raise PermissionDenied()
        if volunteer_application.status != ReviewStatus.NEW:
            raise ValueError('Volunteer application review was already completed')
        volunteer_application.status = ReviewStatus.REJECTED
        volunteer_application.reviewer = request_user
        volunteer_application.review_date = timezone.now()
        ProjectTaskService.save_volunteer_application(request_user, projid, taskid, volunteer_application)
        project_task = volunteer_application.task
        project = project_task.project
        message = "The user {0} has been rejected as volunteer for task {1} of project {2}.".format(volunteer_application.volunteer.standard_display_name(), project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                    message,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.VOLUNTEER_APPLICATION,
                                                    volunteer_application.id)
        NotificationService.add_user_notification(volunteer_application.volunteer,
                                                    "Your volunteer application for task {0} of project {1} has been rejected. The reviewer's comments are: {2}.".format(project_task.name, project.name, volunteer_application.public_reviewer_comments),
                                                    NotificationSeverity.ERROR,
                                                    NotificationSource.VOLUNTEER_APPLICATION,
                                                    volunteer_application.id)
        ProjectService.add_project_change(request_user,
                                          project,
                                          ProjectLogType.REMOVE,
                                          ProjectLogSource.VOLUNTEER_APPLICATION,
                                          volunteer_application.id,
                                          message)

    @staticmethod
    def get_project_task_requirement_importance_levels():
        return TaskRequirementImportance.get_choices()

    @staticmethod
    def get_project_task_staff_for_editing(request_user, projid, taskid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.task_staff_view')
        task_staff_list = ProjectTaskRole.objects.filter(task__id=taskid, role=TaskRole.SUPPORT_STAFF)
        task_staff_dict = {}
        for staff_role in task_staff_list:
            task_staff_dict[staff_role.user.id] = True

        all_project_staff = User.objects.filter(projectrole__project=projid)
        result_staff = []
        for staff_member in all_project_staff:
            result_staff.append({'user': staff_member, 'assigned': task_staff_dict.get(staff_member.id)})
        return result_staff


    @staticmethod
    def set_task_staff(request_user, projid, taskid, post_object):
        project_task = ProjectTask.objects.get(pk=taskid)
        project = Project.objects.get(pk=projid)
        validate_consistent_keys(project_task, (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project, 'project.task_staff_edit')
        task_staff_list = ProjectTaskRole.objects.filter(task__id=taskid, role=TaskRole.SUPPORT_STAFF)
        task_staff_dict = {}
        for staff_role in task_staff_list:
            task_staff_dict[staff_role.user.id] = staff_role

        all_project_staff = User.objects.filter(projectrole__project=projid)
        for staff_member in all_project_staff:
            assigned_form_value = bool(post_object.get(str(staff_member.id)))
            task_role = task_staff_dict.get(staff_member.id)
            if assigned_form_value:
                if not task_role:
                    task_role = ProjectTaskRole()
                    task_role.user = staff_member
                    task_role.task = project_task
                    task_role.role = TaskRole.SUPPORT_STAFF
                    task_role.save()
                    message = "You have been added as support staff of task {0} of project {1}.".format(project_task.name, project.name)
                    NotificationService.add_user_notification(task_role.user,
                                                             message,
                                                             NotificationSeverity.INFO,
                                                             NotificationSource.TASK,
                                                             project_task.id)
            else:
                if task_role:
                    user = task_role.user
                    task_role.delete()
                    message = "You have been removed as support staff from task {0} of project {1}.".format(project_task.name, project.name)
                    NotificationService.add_user_notification(user,
                                                             message,
                                                             NotificationSeverity.WARNING,
                                                             NotificationSource.TASK,
                                                             project_task.id)
        message = "The staff assignments for task {0} of project {1} have changed.".format(project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                 message,
                                                 NotificationSeverity.INFO,
                                                 NotificationSource.TASK,
                                                 project_task.id)
        ProjectService.add_project_change(request_user,
                                           project,
                                           ProjectLogType.EDIT,
                                           ProjectLogSource.TASK,
                                           project_task.id,
                                           message)

    @staticmethod
    def get_project_task_requirements(request_user, projid, taskid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.task_requirements_view')
        task_requirement_list = ProjectTaskRequirement.objects.filter(task__id=taskid)
        task_requirement_dict = {}
        for requirement in task_requirement_list:
            task_requirement_dict[requirement.skill.id] = requirement

        all_skills = Skill.objects.all()
        all_areas = Skill.objects.values('area').distinct()
        result_requirements = {}
        for row in all_areas:
            result_requirements[row['area']] = []
        for skill in all_skills:
            result_requirements[skill.area].append({'system_skill': skill, 'task_requirement': task_requirement_dict.get(skill.id)})
        return result_requirements

    @staticmethod
    def set_task_requirements(request_user, projid, taskid, post_object):
        project_task = ProjectTask.objects.get(pk=taskid)
        validate_consistent_keys(project_task, (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task.project, 'project.task_requirements_edit')
        task_requirement_list = ProjectTaskRequirement.objects.filter(task__id=taskid)
        task_requirement_dict = {}
        for requirement in task_requirement_list:
            task_requirement_dict[requirement.skill.id] = requirement

        all_skills = Skill.objects.all()
        for skill in all_skills:
            level_form_value = int(post_object.get(str(skill.id)))
            if post_object.get("i" + str(skill.id)):
                importance_form_value = int(post_object.get("i" + str(skill.id)))
            else:
                importance_form_value = TaskRequirementImportance.NICE_TO_HAVE
            task_requirement = task_requirement_dict.get(skill.id)
            if level_form_value == -1:
                if task_requirement:
                    task_requirement.delete()
            else:
                if task_requirement:
                    task_requirement.level = level_form_value
                    task_requirement.importance = importance_form_value
                else:
                    task_requirement = ProjectTaskRequirement()
                    task_requirement.skill = skill
                    task_requirement.level = level_form_value
                    task_requirement.importance = importance_form_value
                    task_requirement.task = project_task
                task_requirement.save()
        project = project_task.project
        message = "The requirements for task {0} of project {1} have changed.".format(project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                 message,
                                                 NotificationSeverity.INFO,
                                                 NotificationSource.TASK,
                                                 project_task.id)
        ProjectService.add_project_change(request_user,
                                           project,
                                           ProjectLogType.EDIT,
                                           ProjectLogSource.TASK,
                                           project_task.id,
                                           message)

    @staticmethod
    def get_project_task_role(request_user, projid, taskid, roleid):
        return ProjectTaskRole.objects.get(pk=roleid, task__id=taskid, task__project__id=projid)

    @staticmethod
    def get_own_project_task_role(request_user, projid, taskid):
        return ProjectTaskRole.objects.get(task=taskid, task__id=taskid, task__project__id=projid, user=request_user)

    @staticmethod
    def save_project_task_role(request_user, projid, taskid, project_task_role):
        # Do not check the task ID because we are changing it, so it does not match
        validate_consistent_keys(project_task_role, (['task', 'project', 'id'], projid))
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.volunteers_edit')
        project_task = project_task_role.task
        if project_task.stage == TaskStatus.COMPLETED:
            raise ValueError('Cannot edit the role of a completed task')
        project_task_role.save()
        message = "The volunteer {0} of project {1} has been assigned to the task {2}.".format(project_task_role.user.standard_display_name(), project.name, project_task.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                    message,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.TASK,
                                                    project_task.id)
        NotificationService.add_user_notification(project_task_role.user,
                                                    "Your volunteer spot in project {0} has been changed to task {1}.".format(project.name, project_task.name),
                                                    NotificationSeverity.WARNING,
                                                    NotificationSource.TASK,
                                                    project_task.id)
        ProjectService.add_project_change(request_user,
                                          project,
                                          ProjectLogType.EDIT,
                                          ProjectLogSource.VOLUNTEER,
                                          project_task_role.id,
                                          message)

    @staticmethod
    def delete_project_task_role(request_user, projid, taskid, project_task_role):
        validate_consistent_keys(project_task_role, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.volunteers_remove')
        project_task = project_task_role.task
        if project_task.stage == TaskStatus.COMPLETED:
            raise ValueError('Cannot delete the role of a completed task')
        project_task_role.delete()
        message = "The volunteer {0} has been removed from task {1} of project {2}.".format(project_task_role.user.standard_display_name(), project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                    message,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.TASK,
                                                    project_task.id)
        NotificationService.add_user_notification(project_task_role.user,
                                                    "Your volunteer role for the task {0} of project {1} has been canceled, and you have been removed from the project.".format(project_task.name, project.name),
                                                    NotificationSeverity.ERROR,
                                                    NotificationSource.TASK,
                                                    project_task.id)
        ProjectService.add_project_change(request_user,
                                          project,
                                          ProjectLogType.REMOVE,
                                          ProjectLogSource.VOLUNTEER,
                                          project_task_role.id,
                                          message)

    @staticmethod
    def get_user_in_progress_tasks(request_user):
        return ProjectTask.objects.filter(projecttaskrole__user=request_user,
                                    stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW])

    @staticmethod
    def toggle_task_accepting_volunteers(request_user, projid, taskid):
        project_task = ProjectTaskService.get_project_task(request_user, projid ,taskid)
        if project_task:
           validate_consistent_keys(project_task, (['project', 'id'], projid))
           project = project_task.project
           ensure_user_has_permission(request_user, project, 'project.task_edit')
           project_task.accepting_volunteers = not project_task.accepting_volunteers
           project_task.save()
           if project_task.accepting_volunteers:
               message = "The task {0} of project {1} is now accepting volunteers.".format(project_task.name, project.name)
               NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                        message,
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.PROJECT,
                                                        project.id)
           else:
               message = "The task {0} of project {1} has stopped accepting volunteers.".format(project_task.name, project.name)
               NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                        message,
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.PROJECT,
                                                        project.id)
        else:
           raise KeyError('Project task not found')

    @staticmethod
    def get_task_reviews(request_user, project_task, expand_pinned=False):
        ensure_user_has_permission(request_user, project_task, 'project.all_task_reviews_view')
        base_query = ProjectTaskReview.objects.filter(task=project_task.id)
        if expand_pinned:
            base_query = base_query.annotate(pinnedreview=Count('pinnedtaskreview', fiter=Q(user=request_user)))
        return base_query.order_by('-review_date')

    @staticmethod
    def user_belongs_to_task_review(request_user, task_review):
        return request_user.is_authenticated and ProjectTaskRole.objects.filter(user=request_user, task__projecttaskreview=task_review).exists()

    @staticmethod
    def toggle_pinned_task_review(request_user, projid, taskid, task_reviewid):
        task_review = ProjectTaskReview.objects.get(pk=task_reviewid)
        validate_consistent_keys(task_review, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        ensure_user_has_permission(request_user, task_review, 'project.task_review_pin')
        if task_review:
            pinned_review = PinnedTaskReview.objects.filter(user=request_user, task_review=task_review).first()
            if pinned_review:
                pinned_review.delete()
            else:
                pinned_review = PinnedTaskReview()
                pinned_review.task_review = task_review
                pinned_review.user = request_user
                pinned_review.save()
        else:
            raise KeyError('Task review not found')

    @staticmethod
    def get_pinned_task_reviews(request_user, target_user):
        return PinnedTaskReview.objects.filter(user=target_user)

    @staticmethod
    def publish_project_task(request_user, projid, taskid, project_task):
        validate_consistent_keys(project_task, ('id', taskid), (['project', 'id'], projid))
        project = project_task.project
        ensure_user_has_permission(request_user, project, 'project.task_edit')
        if project_task.stage == TaskStatus.DRAFT:
            project_task.stage = TaskStatus.NOT_STARTED
            project_task.save()
            message = "The project task {0} from project {1} was published by {2}.".format(project_task.name, project.name, request_user.standard_display_name())
            NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                          message,
                                          NotificationSeverity.WARNING,
                                          NotificationSource.TASK,
                                          project_task.id)
            ProjectService.add_project_change(request_user,
                                    project,
                                    ProjectLogType.EDIT,
                                    ProjectLogSource.TASK,
                                    project_task.id,
                                    message)
