from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import date

from ..models.proj import (
    Project, ProjectStatus, ProjectRole, ProjRole, ProjectFollower, ProjectLog, ProjectComment,
    ProjectTask, TaskStatus, TaskRole, ProjectTaskRole, ProjectTaskReview, VolunteerApplication,
    ProjectTaskRequirement, TaskType,
)
from ..models.common import (
    ReviewStatus,
)
from django.db.models import Case, When

from .common import validate_consistent_keys
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
    def get_project_changes(request_user, proj):
        ensure_user_has_permission(request_user, proj, 'project.log_view')
        ## verify user permissions
        return ProjectLog.objects.filter(project = proj).order_by('-change_date')

    @staticmethod
    def get_project_comments(request_user, proj):
        return ProjectComment.objects.filter(project = proj).order_by('-comment_date')

    @staticmethod
    def add_project_comment(request_user, projid, project_comment):
        project = Project.objects.get(pk=projid)
        if project:
            ensure_user_has_permission(request_user, project, 'project.comment_add')
            project_comment.project = project
            project_comment.author = request_user
            try:
                project_comment.save()
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
    def add_staff_member(request_user, projid, project_role):
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.staff_edit')
        if project:
            project_role.project = project
            try:
                project_role.save()
                # NotificationService.add_user_notification(organization_role.user,
                #                                             "You have been added as a member of " + organization_role.organization.name + " with " + organization_role.get_role_display() + " role.",
                #                                             NotificationSeverity.INFO,
                #                                             NotificationSource.ORGANIZATION,
                #                                             organization_role.organization.id)
            except IntegrityError:
                raise ValueError('Duplicate user role')
        else:
            raise KeyError('Project not found ' + str(projid))

    @staticmethod
    def save_project_role(request_user, projid, project_role):
        validate_consistent_keys(project_role, 'Role does not match project', (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_role.project, 'project.staff_edit')
        project_role.save()
        # NotificationService.add_user_notification(organization_role.user,
        #                                             "Your role within " + organization_role.organization.name + " has been changed to " + organization_role.get_role_display() + ".",
        #                                             NotificationSeverity.INFO,
        #                                             NotificationSource.ORGANIZATION,
        #                                             organization_role.organization.id)

    @staticmethod
    def delete_project_role(request_user, projid, project_role):
        validate_consistent_keys(project_role, 'Role does not match project', (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_role.project, 'project.staff_remove')
        project_role.delete()
        # NotificationService.add_user_notification(organization_role.user,
        #                                             "Your role within " + organization_role.organization.name + " has been changed to " + organization_role.get_role_display() + ".",
        #                                             NotificationSeverity.INFO,
        #                                             NotificationSource.ORGANIZATION,
        #                                             organization_role.organization.id)

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
                             When(status=ReviewStatus.REJECTED, then=2)), '-application_date')

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
                                          project=proj).order_by('estimated_start_date')

    @staticmethod
    def get_non_finished_tasks(request_user, proj):
        return ProjectTask.objects.filter(project=proj).exclude(stage=TaskStatus.COMPLETED).exclude(stage=TaskStatus.DELETED).order_by('estimated_start_date')

    @staticmethod
    def get_volunteer_current_tasks(request_user, volunteer, projid): ## TODO check user is the same as volunteer or user is project owner ?
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
        project_task.save()
        # TODO calculate the project status correctly based on all the tasks
        # project_task.project.status = ProjectStatus.WAITING_REVIEW
        # project_task.project.save()
         # TODO move this to a separate method that modifies tasks (so effects are passed on to the project as needed)

    @staticmethod
    def save_task(request_user, projid, taskid, project_task):
        validate_consistent_keys(project_task, 'Task not found in that project', ('id', taskid), (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task.project, 'project.task_edit')
        ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)

    @staticmethod
    def mark_task_as_completed(request_user, projid, taskid, project_task_review):
        project_task = ProjectTask.objects.get(pk=taskid, project__id=projid)
        project = Project.objects.get(pk=projid)
        if project and project_task:
            ensure_user_has_permission(request_user, project_task, 'project.volunteer_task_finish')
            with transaction.atomic():
                project_task_review.task = project_task
                project_task_review.review_result = ReviewStatus.NEW
                project_task_review.save()
                project_task.stage = TaskStatus.WAITING_REVIEW
                ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)
        else:
            if not project:
                raise KeyError('Project not found ' + str(projid))
            else:
                raise KeyError('Task not found ' + str(taskid))

    @staticmethod
    def delete_task(request_user, projid, project_task):
        validate_consistent_keys(project_task, 'Task not found in that project', (['project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task.project, 'project.task_delete')
        project_task.delete()
        # TODO calculate the project status correctly based on all the tasks
        # project_task.project.status = ProjectStatus.WAITING_REVIEW
        # project_task.project.save()
         # TODO move this to a separate method that modifies tasks (so effects are passed on to the project as needed)

    @staticmethod
    def create_default_task(request_user, projid):
        # TODO calculate the project status correctly based on all the tasks
        # project_task.project.status = ProjectStatus.WAITING_REVIEW
        # project_task.project.save()
        # TODO move this to a separate method that modifies tasks (so effects are passed on to the project as needed)
        project = Project.objects.get(pk=projid)
        print("Hello ", project)
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
        with transaction.atomic(): # TODO check that there are no other active volunteers in this task before marking the task as completed? Some data model improvements are needed
            task_review.save()
            if task_review.review_result == ReviewStatus.ACCEPTED:
                project_task.stage = TaskStatus.COMPLETED
                project_task.percentage_complete = 1.0
                project_task.actual_effort_hours = task_review.volunteer_effort_hours
                ProjectTaskService.save_task(request_user, projid, taskid, project_task)
            elif task_review.review_result == ReviewStatus.REJECTED:
                project_task.stage = TaskStatus.STARTED
                ProjectTaskService.save_task(request_user, projid, taskid, project_task)

    @staticmethod
    def accept_task_review(request_user, projid, taskid, task_review): # TODO check that the review request is in status NEW
        validate_consistent_keys(task_review, 'Task review not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        ensure_user_has_permission(request_user, task_review.task.project, 'project.task_review_do')
        task_review.review_result = ReviewStatus.ACCEPTED
        task_review.review_date = timezone.now()
        ProjectTaskService.save_task_review(request_user, projid, taskid, task_review)
        # NotificationService.add_user_notification(membership_request.user,
        #                                             "Congratulations! Your membership request for " + membership_request.organization.name + " was accepted.",
        #                                             NotificationSeverity.INFO,
        #                                             NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST,
        #                                             membership_request.id)

    @staticmethod
    def reject_task_review(request_user, projid, taskid, task_review): # TODO check that the review request is in status NEW
        validate_consistent_keys(task_review, 'Task review not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        ensure_user_has_permission(request_user, task_review.task.project, 'project.task_review_do')
        task_review.review_result = ReviewStatus.REJECTED
        task_review.review_date = timezone.now()
        ProjectTaskService.save_task_review(request_user, projid, taskid, task_review)
        # NotificationService.add_user_notification(membership_request.user,
        #                                             "Congratulations! Your membership request for " + membership_request.organization.name + " was accepted.",
        #                                             NotificationSeverity.INFO,
        #                                             NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST,
        #                                             membership_request.id)

    @staticmethod
    def cancel_volunteering(request_user, projid, taskid, project_task_role):
        validate_consistent_keys(project_task_role, 'Task role not found in that project', (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        ensure_user_has_permission(request_user, project_task_role.task, 'project.volunteer_task_cancel')
        if project_task_role.user != request_user:
            raise ValueError('Role does not match current user')
        else:
            with transaction.atomic():
                project_task = project_task_role.task
                project_task_role.delete()
                if not ProjectTaskService.task_has_volunteers(request_user, taskid):
                    project_task.stage = TaskStatus.STARTED ## or not started?
                    project_task.accepting_volunteers = True
                    ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task)

                # NotificationService.add_user_notification(request_user,
                #                                             "You left " + organization_role.organization.name,
                #                                             NotificationSeverity.INFO,
                #                                             NotificationSource.ORGANIZATION,
                #                                             organization_role.organization.id)
                # admins = OrganizationService.get_organization_admins(request_user, organization_role.organization)
                # NotificationService.add_multiuser_notification(admins,
                #                                             organization_role.user.first_name + " " + organization_role.user.last_name + " left " + organization_role.organization.name,
                #                                             NotificationSeverity.INFO,
                #                                             NotificationSource.ORGANIZATION,
                #                                             organization_role.organization.id)


    @staticmethod
    def apply_to_volunteer(request_user, projid, taskid, task_application_request): # TODO check the user is not already accepted for the task
        # TODO check the user has a volunteer profile
        project_task = ProjectTask.objects.get(pk=taskid, project__id=projid)
        validate_consistent_keys(project_task, 'Task not found in that project', (['project', 'id'], projid))
        task_application_request.status = ReviewStatus.NEW
        task_application_request.task = project_task
        task_application_request.volunteer = request_user
        task_application_request.save()

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

    # TODO remove all the permission validation in accept/reject methods that delegate on a save method? Document it clearly
    @staticmethod
    def accept_volunteer(request_user, projid, taskid, volunteer_application): # TODO check that the review request is in status NEW
        validate_consistent_keys(volunteer_application, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        volunteer_application.status = ReviewStatus.ACCEPTED
        volunteer_application.review_date = timezone.now()
        ProjectTaskService.save_volunteer_application(request_user, projid, taskid, volunteer_application)
        # NotificationService.add_user_notification(membership_request.user,
        #                                             "Congratulations! Your membership request for " + membership_request.organization.name + " was accepted.",
        #                                             NotificationSeverity.INFO,
        #                                             NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST,
        #                                             membership_request.id)

    @staticmethod
    def reject_volunteer(request_user, projid, taskid, volunteer_application): # TODO check that the review request is in status NEW
        validate_consistent_keys(volunteer_application, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        volunteer_application.status = ReviewStatus.REJECTED
        volunteer_application.review_date = timezone.now()
        ProjectTaskService.save_volunteer_application(request_user, projid, taskid, volunteer_application)
        # NotificationService.add_user_notification(membership_request.user,
        #                                             "Congratulations! Your membership request for " + membership_request.organization.name + " was accepted.",
        #                                             NotificationSeverity.INFO,
        #                                             NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST,
        #                                             membership_request.id)


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
        requirement.task = project_task
        requirement.save()

    @staticmethod
    def save_task_requirement(request_user, projid, taskid, requirement):
        validate_consistent_keys(requirement, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.task_requirements_edit')
        requirement.save()

    @staticmethod
    def delete_task_requirement(request_user, projid, taskid, requirement):
        validate_consistent_keys(requirement, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.task_requirements_delete')
        requirement.delete()

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
        project_task_role.save()
        # NotificationService.add_user_notification(organization_role.user,
        #                                             "Your role within " + organization_role.organization.name + " has been changed to " + organization_role.get_role_display() + ".",
        #                                             NotificationSeverity.INFO,
        #                                             NotificationSource.ORGANIZATION,
        #                                             organization_role.organization.id)

    @staticmethod
    def delete_project_task_role(request_user, projid, taskid, project_task_role):
        validate_consistent_keys(project_task_role, (['task', 'id'], taskid), (['task', 'project', 'id'], projid))
        project = Project.objects.get(pk=projid)
        ensure_user_has_permission(request_user, project, 'project.volunteers_remove')
        project_task_role.delete()
        # NotificationService.add_user_notification(organization_role.user,
        #                                             "Your role within " + organization_role.organization.name + " has been changed to " + organization_role.get_role_display() + ".",
        #                                             NotificationSeverity.INFO,
        #                                             NotificationSource.ORGANIZATION,
        #                                             organization_role.organization.id)
