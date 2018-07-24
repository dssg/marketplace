from rules import add_perm, predicate

from dssgmkt.domain.proj import ProjectService, ProjectTaskService
from dssgmkt.domain.user import UserService


add_perm('project.view', ProjectService.is_project_visible_by_user)
add_perm('project.information_edit', ProjectService.user_is_project_owner)
add_perm('project.publish', ProjectService.user_is_project_owner)
add_perm('project.approve_as_completed', ProjectService.user_is_project_official)
add_perm('project.scope_view', ProjectService.is_project_visible_by_user)
add_perm('project.scope_edit', ProjectService.user_is_project_official)
add_perm('project.log_view', ProjectService.user_is_project_member)
add_perm('project.comment_add', ProjectService.user_is_channel_commenter)
add_perm('project.volunteer_instructions_view', ProjectService.user_is_project_volunteer)
add_perm('project.volunteer_task_finish', ProjectTaskService.user_is_task_volunteer)
add_perm('project.volunteer_task_cancel', ProjectTaskService.user_is_task_volunteer)
add_perm('project.task_review_view', ProjectService.user_is_project_member)
add_perm('project.task_review_pin', ProjectTaskService.user_belongs_to_task_review)
add_perm('project.task_review_do', ProjectService.user_is_project_official) # or user is task editor? do we let project managers to review task completion?
add_perm('project.tasks_view', ProjectService.user_is_project_member)
add_perm('project.task_edit', ProjectService.user_is_task_editor)
add_perm('project.task_apply', UserService.user_has_approved_volunteer_profile)
add_perm('project.task_requirements_view', ProjectService.user_is_task_editor)
add_perm('project.task_requirements_edit', ProjectService.user_is_task_editor)
add_perm('project.task_requirements_delete', ProjectService.user_is_task_editor)
add_perm('project.task_staff_view', ProjectService.user_is_project_member)
add_perm('project.task_staff_edit', ProjectService.user_is_project_owner)
add_perm('project.task_delete', ProjectService.user_is_task_editor)
add_perm('project.staff_view', ProjectService.user_is_project_official)
add_perm('project.staff_edit', ProjectService.user_is_project_owner)
add_perm('project.staff_remove', ProjectService.user_is_project_owner)
add_perm('project.volunteers_view', ProjectService.user_is_project_official)
add_perm('project.volunteers_edit', ProjectService.user_is_project_official)
add_perm('project.volunteers_remove', ProjectService.user_is_project_official)
add_perm('project.volunteers_application_view', ProjectTaskService.user_can_view_volunteer_application)
add_perm('project.volunteers_application_review', ProjectService.user_is_project_official) # or user is task editor?
