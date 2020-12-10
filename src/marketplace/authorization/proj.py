from rules import add_perm, predicate

from marketplace.domain import marketplace
from marketplace.domain.proj import ProjectService, ProjectTaskService
from marketplace.domain.user import UserService


add_perm('project.view', marketplace.project.user.can_view)
add_perm('project.information_edit', marketplace.project.user.can_edit_information)
add_perm('project.publish', marketplace.project.user.is_owner)
add_perm('project.approve_as_completed', marketplace.project.user.can_complete)
add_perm('project.scope_view', marketplace.project.user.can_view)
add_perm('project.scope_edit', marketplace.project.user.is_official)
add_perm('project.log_view', marketplace.project.user.is_member)
add_perm('project.comment_add', marketplace.project.user.is_channel_commenter)
add_perm('project.volunteer_instructions_view', marketplace.project.user.is_volunteer)
add_perm('project.volunteer_task_finish', ProjectTaskService.user_is_task_volunteer)
add_perm('project.volunteer_task_cancel', ProjectTaskService.user_is_task_volunteer)
add_perm('project.all_task_reviews_view', ProjectTaskService.user_can_view_all_task_reviews)
add_perm('project.task_review_view', ProjectTaskService.user_can_view_task_review)
add_perm('project.task_review_pin', ProjectTaskService.user_belongs_to_task_review)
add_perm('project.task_review_do', marketplace.project.user.can_review_tasks)
add_perm('project.tasks_view', marketplace.project.user.can_view_tasks)
add_perm('project.task_edit', marketplace.project.user.is_task_editor)
add_perm('project.task_apply', UserService.user_has_approved_volunteer_profile)
add_perm('project.task_requirements_view', marketplace.project.user.is_task_editor)
add_perm('project.task_requirements_edit', marketplace.project.user.is_task_editor)
add_perm('project.task_requirements_delete', marketplace.project.user.is_task_editor)
add_perm('project.task_staff_view', marketplace.project.user.is_member)
add_perm('project.task_staff_edit', marketplace.project.user.is_owner)
add_perm('project.task_delete', marketplace.project.user.is_task_editor)
add_perm('project.staff_view', marketplace.project.user.is_official)
add_perm('project.staff_edit', marketplace.project.user.is_owner)
add_perm('project.staff_remove', marketplace.project.user.is_owner)
add_perm('project.volunteers_view', marketplace.project.user.is_official)
add_perm('project.volunteers_edit', marketplace.project.user.is_official)
add_perm('project.volunteers_remove', marketplace.project.user.is_official)
add_perm('project.volunteers_application_view', ProjectTaskService.user_can_view_volunteer_application)
add_perm('project.volunteers_application_review', marketplace.project.user.is_official) # or user is task editor?
