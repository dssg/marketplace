from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import date

from ..models.proj import (
    Project, ProjectStatus, ProjectRole, ProjRole, ProjectFollower, ProjectLog, ProjectLogType, ProjectLogSource, ProjectComment,
    ProjectTask, TaskStatus, TaskRole, ProjectTaskRole, ProjectTaskReview, VolunteerApplication,
    ProjectTaskRequirement, TaskType,
)
from ..models.common import (
    ReviewStatus,
)
from ..models.user import (
    User, NotificationSeverity, NotificationSource, VolunteerProfile,
)
from django.db.models import Case, When

from .common import validate_consistent_keys
from .notifications import NotificationService
from dssgmkt.authorization.common import ensure_user_has_permission

def filter_public_projects(query_set):
    return query_set.exclude(status=ProjectStatus.DRAFT) \
                    .exclude(status=ProjectStatus.EXPIRED) \
                    .exclude(status=ProjectStatus.DELETED)

class ProjectService():
    @staticmethod
    def get_project(request_user, projid):
        return Project.objects.get(pk=projid)

    @staticmethod
    def get_all_projects(request_user):
        # We could also add the projects that are non-public but that also belong
        # to the organizations that the user is member of. Should that be added
        # or should users access those projects through the page of their org?
        return filter_public_projects(Project.objects.all())

    @staticmethod
    def get_all_organization_projects(request_user, org):
        return Project.objects.filter(organization=org)

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
    def is_project_visible_by_user(user, project):
        if project.status == ProjectStatus.DRAFT:
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
    def get_project_changes(request_user, proj):
        ensure_user_has_permission(request_user, proj, 'project.log_view')
        return ProjectLog.objects.filter(project = proj).order_by('-change_date')

    @staticmethod
    def get_project_comments(request_user, proj):
        return ProjectComment.objects.filter(project = proj).order_by('-comment_date')

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
    def add_project_comment(request_user, projid, project_comment):
        project = Project.objects.get(pk=projid)
        if project:
            ensure_user_has_permission(request_user, project, 'project.comment_add')
            project_comment.project = project
            project_comment.author = request_user
            try:
                project_comment.save()
                NotificationService.add_multiuser_notification(ProjectService.get_public_notification_users(request_user, project),
                                                            "New comment added to the discussion of project {0}.".format(project.name),
                                                            NotificationSeverity.INFO,
                                                            NotificationSource.PROJECT,
                                                            project.id)
            except IntegrityError:
                raise ValueError('Cannot save comment')
        else:
            raise KeyError('Project not found ' + str(projid))

    @staticmethod
    def save_project(request_user, projid, project):
        validate_consistent_keys(project, ('id', projid))
        ensure_user_has_permission(request_user, project, 'project.information_edit')
        project.save()

    @staticmethod
    def publish_project(request_user, projid, project):
        validate_consistent_keys(project, ('id', projid))
        ensure_user_has_permission(request_user, project, 'project.publish')
        if project.status == ProjectStatus.DRAFT:
            project.status = ProjectStatus.NEW
            project.save()

    @staticmethod
    def finish_project(request_user, projid, project):
        validate_consistent_keys(project, ('id', projid))
        ensure_user_has_permission(request_user, project, 'project.approve_as_completed')
        if project.status == ProjectStatus.WAITING_REVIEW:
            project.status = ProjectStatus.COMPLETED
            project.save()

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
    def get_all_project_staff(request_user, projid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.staff_view')
        return ProjectRole.objects.filter(project=projid).order_by('role')

    @staticmethod
    def get_all_project_volunteers(request_user, projid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.volunteers_view')
        return ProjectTaskRole.objects.filter(task__project__id=projid)

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
        return Project.objects.filter(projectrole__user=request_user,
                                      projectrole__role=ProjRole.OWNER,
                                      projecttask__projecttaskreview__review_result=ReviewStatus.NEW
                        ).union(Project.objects.filter(
                            projecttask__projecttaskrole__user=request_user,
                            projecttask__stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW],
                            projecttask__type__in=[TaskType.SCOPING_TASK, TaskType.PROJECT_MANAGEMENT_TASK],
                            projecttask__projecttaskreview__review_result=ReviewStatus.NEW
                        )).distinct()

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
                                          project=proj).exclude(stage=TaskStatus.COMPLETED).order_by('estimated_start_date')

    @staticmethod
    def get_non_finished_tasks(request_user, proj):
        return ProjectTask.objects.filter(project=proj).exclude(stage=TaskStatus.COMPLETED).exclude(stage=TaskStatus.DELETED).order_by('estimated_start_date')

    @staticmethod
    def get_volunteer_current_tasks(request_user, volunteer, projid):
        ensure_user_has_permission(request_user, volunteer, 'user.is_same_user')
        return ProjectTask.objects.filter(project__pk=projid,
                                          projecttaskrole__user=volunteer,
                                          stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW])

    @staticmethod
    def get_volunteer_all_tasks(request_user, target_user):
        return ProjectTask.objects.filter(projecttaskrole__user=target_user).exclude(project__status=ProjectStatus.DRAFT)

    @staticmethod
    def user_is_task_volunteer(user, task):
        return user.is_authenticated and ProjectTaskRole.objects.filter(user=user, role=TaskRole.VOLUNTEER, task=task).exists()

    @staticmethod
    def user_can_view_volunteer_application(user, volunteer_application):
        return user == volunteer_application.volunteer or ProjectService.user_is_project_official(user, volunteer_application.task.project)

    @staticmethod
    def user_can_review_task(user, task): # TODO use this for the authorization of task_review_do ?
        return ProjectService.user_is_project_official(user, task.project) and not ProjectTaskRole.objects.filter(user=user, task=task).exists()

    @staticmethod
    def task_has_volunteers(request_user, taskid):
        return ProjectTaskRole.objects.filter(task=taskid, role=TaskRole.VOLUNTEER).exists()

    @staticmethod
    def save_task_internal(request_user, projid, taskid, project_task):
        with transaction.atomic():
            current_task = ProjectTask.objects.get(pk=project_task.id)
            project_task.save()
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
                    elif project_task.stage == TaskStatus.WAITING_REVIEW:
                        if project.status == ProjectStatus.DESIGN:
                            # Move the project to status waiting design review
                            project.status = ProjectStatus.WAITING_DESIGN_APPROVAL
                            project.save()
                elif project_task.type == TaskType.PROJECT_MANAGEMENT_TASK:
                    pass
                else:
                    if project_task.stage == TaskStatus.COMPLETED:
                        # Check that there are no more open tasks, then move the project to waiting review stage
                        with_open_tasks = ProjectTask.objects.filter(project=project).exclude(stage=TaskStatus.COMPLETED).exists()
                        if not with_open_tasks:
                            project.status = ProjectStatus.WAITING_REVIEW
                            project.save()


    @staticmethod
    def save_task(request_user, projid, taskid, project_task):
        validate_consistent_keys(project_task, 'Task not found in that project', ('id', taskid), (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task.project, 'project.task_edit')
        if project_task.stage == TaskStatus.COMPLETED:
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
            with transaction.atomic():
                project_task_review.task = project_task
                project_task_review.volunteer = request_user
                project_task_review.review_result = ReviewStatus.NEW
                project_task_review.save()
                project_task.stage = TaskStatus.WAITING_REVIEW
                ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)
            message = "The task {0} from project {1} has been marked as completed by the volunteer and needs to be reviewed.".format(project_task.name, project.name)
            NotificationService.add_multiuser_notification(ProjectService.get_project_officials(request_user, project),
                                                        message,
                                                        NotificationSeverity.WARNING,
                                                        NotificationSource.TASK,
                                                        project_task.id)
            NotificationService.add_user_notification(request_user,
                                                        "You marked task {0} of project {1} as finished. The project staff will review it and you will be notified when the QA .".format(project_task.name, project.name),
                                                        NotificationSeverity.INFO,
                                                        NotificationSource.TASK,
                                                        project_task.id) # TODO change this to notify all the volunteers working on this task
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
        project_task.delete()
        # TODO What happens with volunteers working on this task? Do not allow deleting tasks with volunteers
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
            project_task.description = 'This is the task description'
            project_task.onboarding_instructions = 'These are the volunteer onboarding instructions'
            project_task.stage = TaskStatus.NOT_STARTED
            project_task.accepting_volunteers = False
            project_task.project = project
            project_task.percentage_complete = 0
            project_task.business_area = 'no'
            project_task.estimated_start_date = date.today()
            project_task.estimated_end_date = date.today()
            project_task.save()
            if project.status == ProjectStatus.WAITING_REVIEW:
                project.status = ProjectStatus.IN_PROGRESS
                project.save()
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
        ensure_user_has_permission(request_user, project, 'project.task_review_view')
        task_review = ProjectTaskReview.objects.get(pk=reviewid)
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
                ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)
            elif task_review.review_result == ReviewStatus.REJECTED:
                project_task.stage = TaskStatus.STARTED
                ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)

    @staticmethod
    def accept_task_review(request_user, projid, taskid, task_review):
        validate_consistent_keys(task_review, 'Task review not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        ensure_user_has_permission(request_user, task_review.task.project, 'project.task_review_do')
        if task_review.review_result != ReviewStatus.NEW:
            raise ValueError('Task review was already completed')
        task_review.review_result = ReviewStatus.ACCEPTED
        task_review.review_date = timezone.now()
        ProjectTaskService.save_task_review(request_user, projid, taskid, task_review)
        project_task = task_review.task
        project = project_task.project
        message = "The task {0} from project {1} has been accepted during QA phase and it's now completed.".format(project_task.name, project.name)
        NotificationService.add_multiuser_notification(ProjectService.get_project_members(request_user, project),
                                                    message,
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.TASK,
                                                    project_task.id)
        NotificationService.add_user_notification(task_review.volunteer,
                                                    "Congratulations! Your task {0} of project {1} has been reviewed by the project staff and accepted as finished, so your work has been completed. The staff comments are: {2}.".format(project_task.name, project.name, task_review.public_reviewer_comments),
                                                    NotificationSeverity.INFO,
                                                    NotificationSource.TASK,
                                                    project_task.id) # TODO change this to notify all the volunteers working on this task, not just the one that marked it as completed
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

    @staticmethod
    def cancel_volunteering(request_user, projid, taskid, project_task_role):
        validate_consistent_keys(project_task_role, 'Task role not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task_role.task, 'project.volunteer_task_cancel')
        if project_task_role.user != request_user:
            raise ValueError('Role does not match current user')
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
        project_task = ProjectTask.objects.get(pk=taskid, project__id=projid)
        validate_consistent_keys(project_task, 'Task not found in that project', (['project', 'id'], projid))
        if ProjectTaskService.user_is_task_volunteer(request_user, project_task):
            raise ValueException('User is already a volunteer of this task')
        if not VolunteerProfile.objects.filter(user=request_user).exists(): # We cannot call UserService.user_has_volunteer_profile because a circular dependency
            raise ValueException('User is not a volunteer')
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
        volunteer_application = VolunteerApplication.objects.get(pk=volunteer_application_pk, task__id=taskid, task__project__id=projid)
        ensure_user_has_permission(request_user, volunteer_application, 'project.volunteers_application_view')
        ## We can avoid doing this by using all the constraints in the DB query
        # volunteer_application = VolunteerApplication.objects.get(pk=volunteer_application_pk)
        # validate_consistent_keys(volunteer_application, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        # return volunteer_application
        ## ... like so
        return volunteer_application # TODO fix comment right above

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
                    project_task.save()
                if project.status == ProjectStatus.NEW:
                    if project_task.type == TaskType.SCOPING_TASK:
                        # Move project to status scoping
                        project.status = ProjectStatus.DESIGN
                        project.save()
                elif project.status == ProjectStatus.WAITING_STAFF:
                    if project_task.type == TaskType.DOMAIN_WORK_TASK:
                        # Move project to status in progress
                        project.status = ProjectStatus.IN_PROGRESS
                        project.save()

    # TODO remove all the permission validation in accept/reject methods that delegate on a save method? Document it clearly
    @staticmethod
    def accept_volunteer(request_user, projid, taskid, volunteer_application):
        validate_consistent_keys(volunteer_application, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        if volunteer_application.status != ReviewStatus.NEW:
            raise ValueError('Volunteer application review was already completed')
        volunteer_application.status = ReviewStatus.ACCEPTED
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
        if volunteer_application.status != ReviewStatus.NEW:
            raise ValueError('Volunteer application review was already completed')
        volunteer_application.status = ReviewStatus.REJECTED
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
    def get_project_task_requirements(request_user, projid, taskid):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.task_requirements_view')
        return ProjectTaskRequirement.objects.filter(task=taskid, task__project__id=projid)

    @staticmethod
    def add_task_requirement(request_user, projid, taskid, requirement):
        project_task = ProjectTask.objects.get(pk=taskid)
        validate_consistent_keys(project_task, (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task.project, 'project.task_requirements_edit')
        if project_task.stage == TaskStatus.COMPLETED:
            raise ValueError('Cannot edit a completed task')
        requirement.task = project_task
        try:
            requirement.save()
        except IntegrityError:
            raise KeyError('Duplicate task requirement')
        project = project_task.project
        message = "A new requirement ({0}) was added to task {1} of project {2}.".format(requirement.standard_display_name(), project_task.name, project.name)
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
    def save_task_requirement(request_user, projid, taskid, requirement):
        validate_consistent_keys(requirement, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.task_requirements_edit')
        project_task = requirement.task
        if project_task.stage == TaskStatus.COMPLETED:
            raise ValueError('Cannot edit a completed task')
        requirement.save()
        message = "The task requirement {0} of task {1} of project {2} was edited.".format(requirement.standard_display_name(), project_task.name, project.name)
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
    def delete_task_requirement(request_user, projid, taskid, requirement):
        validate_consistent_keys(requirement, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.task_requirements_delete')
        project_task = requirement.task
        if project_task.stage == TaskStatus.COMPLETED:
            raise ValueError('Cannot edit a completed task')
        requirement.delete()
        message = "The task requirement {0} of task {1} of project {2} was deleted.".format(requirement.standard_display_name(), project_task.name, project.name)
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
