from django.db import transaction
from django.utils import timezone

from ..models.proj import (
    Project, ProjectStatus, ProjectRole, ProjRole, ProjectFollower, ProjectLog, ProjectComment,
    ProjectTask, TaskStatus, TaskRole, ProjectTaskRole,
)
from ..models.common import (
    ReviewStatus,
)


def filter_public_projects(query_set):
    return query_set.exclude(status=ProjectStatus.DRAFT) \
                    .exclude(status=ProjectStatus.EXPIRED) \
                    .exclude(status=ProjectStatus.DELETED)

class ProjectService():
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
    def user_is_project_member(user, proj):
        return user.is_authenticated and ProjectRole.objects.filter(project=proj, user=user).exists()

    @staticmethod
    def user_is_project_owner(user, proj):
        return user.is_authenticated and ProjectRole.objects.filter(project=proj, user=user, role=ProjRole.OWNER).exists()

    @staticmethod
    def user_is_project_follower(user, proj):
        return user.is_authenticated and ProjectFollower.objects.filter(project=proj, user=user).exists()

    @staticmethod
    def get_project_changes(request_user, proj):
        ## verify user permissions
        return ProjectLog.objects.filter(project = proj).order_by('-change_date')

    @staticmethod
    def get_project_comments(request_user, proj):
        return ProjectComment.objects.filter(project = proj).order_by('-comment_date')

    @staticmethod
    def add_project_comment(request_user, projid, project_comment):
        project = Project.objects.get(pk=projid)
        if project:
            project_comment.project = project
            project_comment.author = request_user
            try:
                project_comment.save()
            except IntegrityError:
                raise ValueError('Cannot save comment')
        else:
            raise KeyError('Project not found ' + str(projid))

class ProjectTaskService():
    @staticmethod
    def get_open_tasks(request_user, proj):
        return ProjectTask.objects.filter(accepting_volunteers = True,
                                          project = proj).order_by('estimated_start_date')


    @staticmethod
    def get_volunteer_current_tasks(request_user, volunteer, projid):
        return ProjectTask.objects.filter(project__pk=projid,
                                          projecttaskrole__user=volunteer,
                                          stage__in=[TaskStatus.STARTED, TaskStatus.WAITING_REVIEW])

    @staticmethod
    def task_has_volunteers(request_user, taskid):
        return ProjectTaskRole.objects.filter(task=taskid, role=TaskRole.VOLUNTEER).exists()

    @staticmethod
    def save_task(request_user, project_task):
        project_task.save()
        # TODO calculate the project status correctly based on all the tasks
        # project_task.project.status = ProjectStatus.WAITING_REVIEW
        # project_task.project.save()
         # TODO move this to a separate method that modifies tasks (so effects are passed on to the project as needed)

    @staticmethod
    def mark_task_as_completed(request_user, projid, taskid, project_task_review):
        project_task = ProjectTask.objects.get(pk=taskid)
        project = Project.objects.get(pk=projid)
        if project and project_task:
            with transaction.atomic():
                project_task_review.task = project_task
                project_task_review.review_result = ReviewStatus.NEW
                project_task_review.save()
                project_task.stage = TaskStatus.WAITING_REVIEW
                ProjectTaskService.save_task(request_user, project_task)
        else:
            if not project:
                raise KeyError('Project not found ' + str(projid))
            else:
                raise KeyError('Task not found ' + str(taskid))


    @staticmethod
    def save_task_review(request_user, projid, taskid, task_review):
        project_task = ProjectTask.objects.get(pk=taskid)
        project = Project.objects.get(pk=projid)
        if project and project_task and task_review.task == project_task and task_review.task.project == project:
            with transaction.atomic():
                task_review.save()
                if task_review.review_result == ReviewStatus.ACCEPTED:
                    project_task.stage = TaskStatus.COMPLETED
                    project_task.percentage_complete = 1.0
                    project_task.actual_effort_hours = task_review.volunteer_effort_hours
                    ProjectTaskService.save_task(request_user, project_task)
                elif task_review.review_result == ReviewStatus.REJECTED:
                    project_task.stage = TaskStatus.STARTED
                    ProjectTaskService.save_task(request_user, project_task)
        else:
            raise ValueError('Task review does not match project or task')

    @staticmethod
    def accept_task_review(request_user, projid, taskid, task_review): # TODO check that the review request is in status NEW
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
        if project_task_role.task.id != taskid:
            raise ValueError('Role does not match task')
        elif project_task_role.task.project.id != projid:
            raise ValueError('Role does not match project')
        elif project_task_role.user != request_user:
            raise ValueError('Role does not match current user')
        else:
            with transaction.atomic():
                project_task = project_task_role.task
                project_task_role.delete()
                if not ProjectTaskService.task_has_volunteers(request_user, taskid):
                    project_task.stage = TaskStatus.STARTED ## or not started?
                    project_task.accepting_volunteers = True
                    ProjectTaskService.save_task(request_user, project_task)

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
