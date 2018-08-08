from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

from dssgmkt.models.common import ReviewStatus
from dssgmkt.models.proj import (
    ProjectRole, ProjRole, TaskType, VolunteerApplication, ProjectScope,
    TaskStatus, ProjectComment,
)
from dssgmkt.models.user import SignupCodeType, SignupCode
from dssgmkt.domain.user import UserService
from dssgmkt.domain.org import OrganizationService
from dssgmkt.domain.proj import ProjectService, ProjectTaskService

from dssgmkt.tests.domain.common import (
    example_organization_user, example_staff_user, example_volunteer_user,
    example_organization, example_project,
    test_users_group_inclusion, test_permission_denied_operation,
)


class ProjectTestCase(TestCase):
    owner_user = None
    staff_user = None
    volunteer_user = None
    scoping_user = None
    proj_mgmt_user = None
    organization = None
    project = None

    def setUp(self):
        code = SignupCode()
        code.name = "AUTOMATICVOLUNTEER"
        code.type = SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT
        code.save()

        self.owner_user = example_organization_user()
        UserService.create_user(None, self.owner_user, 'organization', None)

        self.staff_user = example_staff_user()
        UserService.create_user(None, self.staff_user, 'organization', None)

        self.volunteer_user = example_volunteer_user()
        self.volunteer_user.special_code = "AUTOMATICVOLUNTEER"
        UserService.create_user(None, self.volunteer_user, 'volunteer', None)
        UserService.create_volunteer_profile(self.volunteer_user, self.volunteer_user.id)

        self.scoping_user = example_volunteer_user(username="scopinguser")
        self.scoping_user.special_code = "AUTOMATICVOLUNTEER"
        UserService.create_user(None, self.scoping_user, 'volunteer', None)
        UserService.create_volunteer_profile(self.scoping_user, self.scoping_user.id)

        self.proj_mgmt_user = example_volunteer_user(username="managementuser")
        self.proj_mgmt_user.special_code = "AUTOMATICVOLUNTEER"
        UserService.create_user(None, self.proj_mgmt_user, 'volunteer', None)
        UserService.create_volunteer_profile(self.proj_mgmt_user, self.proj_mgmt_user.id)

        self.organization = example_organization()
        OrganizationService.create_organization(self.owner_user, self.organization)
        OrganizationService.add_staff_member_by_id(self.owner_user, self.organization.id, self.staff_user.id, None)

        self.project = example_project()

    def test_create_project(self):
        self.assertEqual(list(ProjectService.get_all_public_projects(self.owner_user, None)), [])
        self.assertEqual(list(ProjectService.get_all_organization_projects(self.owner_user, self.organization)), [])
        self.assertEqual(list(ProjectService.get_organization_public_projects(self.owner_user, self.organization)), [])
        self.assertEqual(ProjectService.get_project(self.owner_user, 1), None)
        self.assertEqual(ProjectService.get_featured_project(), None)
        self.assertEqual(list(ProjectService.get_user_projects_in_draft_status(self.owner_user)), [])
        self.assertEqual(list(ProjectService.get_user_projects_in_draft_status(self.volunteer_user)), [])

        # Test that the create project operation works
        test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user],
            lambda x: OrganizationService.create_project(x, self.organization.id, self.project))
        OrganizationService.create_project(self.owner_user, self.organization.id, self.project)

        projects_list = [self.project]
        self.assertEqual(list(ProjectService.get_all_public_projects(self.owner_user, None)), [])
        self.assertEqual(list(ProjectService.get_all_organization_projects(self.owner_user, self.organization)), projects_list)
        self.assertEqual(list(ProjectService.get_organization_public_projects(self.owner_user, self.organization)), [])
        self.assertEqual(ProjectService.get_featured_project(), None)
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id), self.project)
        self.assertTrue(ProjectService.is_project_visible_by_user(self.owner_user, self.project))
        self.assertFalse(ProjectService.is_project_visible_by_user(self.staff_user, self.project))
        self.assertFalse(ProjectService.is_project_visible_by_user(self.volunteer_user, self.project))
        self.assertFalse(ProjectService.is_project_visible_by_user(AnonymousUser(), self.project))
        self.assertEqual(list(ProjectService.get_user_projects_in_draft_status(self.owner_user)), projects_list)
        self.assertEqual(list(ProjectService.get_user_projects_in_draft_status(self.volunteer_user)), [])

        # Test that we can edit the project
        self.project.name = "EDITED demo project 1"
        test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user],
            lambda x: ProjectService.save_project(x, self.project.id, self.project))
        ProjectService.save_project(self.owner_user, self.project.id, self.project)
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id), self.project)

        # Test that we can publish the project
        test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user],
            lambda x: ProjectService.publish_project(x, self.project.id, self.project))
        ProjectService.publish_project(self.owner_user, self.project.id, self.project)

        self.assertEqual(list(ProjectService.get_all_public_projects(self.owner_user, None)), [self.project])
        self.assertEqual(list(ProjectService.get_all_organization_projects(self.owner_user, self.organization)), projects_list)
        self.assertEqual(list(ProjectService.get_organization_public_projects(self.owner_user, self.organization)), projects_list)
        self.assertEqual(ProjectService.get_featured_project(), self.project)
        self.assertEqual(list(ProjectService.get_user_projects_in_draft_status(self.owner_user)), [])

    def create_standard_project_structure(self):
        OrganizationService.create_project(self.owner_user, self.organization.id, self.project)
        ProjectService.publish_project(self.owner_user, self.project.id, self.project)
        staff_user_role = ProjectRole()
        staff_user_role.user = self.staff_user
        staff_user_role.project = self.project
        staff_user_role.role = ProjRole.STAFF

        # Test adding staff members
        test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user],
            lambda x: ProjectService.add_staff_member(x, self.project.id, staff_user_role))
        ProjectService.add_staff_member(self.owner_user, self.project.id, staff_user_role)

        # For each task of the project, we 1) make it public, 2) allow volunteers
        # to apply, 3) apply to it with a volunteer user, and 4) accept the
        # volunteer application. Each task gets a different user so we can test
        # their permissions appropriately later.
        tasks = ProjectTaskService.get_all_tasks(self.owner_user, self.project)
        scoping_task = None
        project_management_task = None
        domain_work_task = None
        volunteer_applications = []
        for task in tasks:
            ProjectTaskService.publish_project_task(self.owner_user, self.project.id, task.id, task)
            ProjectTaskService.toggle_task_accepting_volunteers(self.owner_user, self.project.id, task.id)
            application = VolunteerApplication()
            application.volunteer_application_letter = "This is the letter."
            application.task = task
            if task.type == TaskType.SCOPING_TASK:
                scoping_task = task
                application.volunteer = self.scoping_user
            elif task.type == TaskType.PROJECT_MANAGEMENT_TASK:
                project_management_task = task
                application.volunteer = self.proj_mgmt_user
            elif task.type == TaskType.DOMAIN_WORK_TASK:
                domain_work_task = task
                application.volunteer = self.volunteer_user
            ProjectTaskService.apply_to_volunteer(application.volunteer, self.project.id, task.id, application)
            self.assertEqual(list(ProjectService.get_user_projects_with_pending_volunteer_requests(self.owner_user)), [self.project])
            ProjectTaskService.accept_volunteer(self.owner_user, self.project.id, task.id, application)
            self.assertEqual(list(ProjectService.get_user_projects_with_pending_volunteer_requests(self.owner_user)), [])
            volunteer_applications.append(application)
        self.assertEqual(set(ProjectService.get_all_volunteer_applications(self.owner_user, self.project.id)), set(volunteer_applications))

    def test_project_roles(self):
        self.create_standard_project_structure()

        # Check the membership of users to the various user groups that exist in projects
        all_users = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user]
        self.assertEqual(set(ProjectService.get_all_project_users(self.owner_user, self.project)), set(all_users))
        self.assertEqual(set(ProjectService.get_public_notification_users(self.owner_user, self.project)), set(all_users))

        owner_users = [self.owner_user]
        with self.subTest(stage='Owner users'):
            test_users_group_inclusion(self, all_users, owner_users, lambda x: ProjectService.user_is_project_owner(x, self.project))

        owner_user_roles = [self.owner_user.projectrole_set.first()]
        with self.subTest(stage='Owner user roles'):
            self.assertEqual(set(ProjectService.get_project_owners(self.owner_user, self.project.id)), set(owner_user_roles))

        staff_user_roles = [self.owner_user.projectrole_set.first(), self.staff_user.projectrole_set.first()]
        with self.subTest(stage='Staff user roles'):
            self.assertEqual(set(ProjectService.get_all_project_staff(self.owner_user, self.project.id)), set(staff_user_roles))

        volunteer_users = [self.scoping_user, self.proj_mgmt_user, self.volunteer_user]
        with self.subTest(stage='Volunteer users'):
            test_users_group_inclusion(self, all_users, volunteer_users, lambda x: ProjectService.user_is_project_volunteer(x, self.project))
            test_users_group_inclusion(self, all_users, volunteer_users, ProjectService.user_is_volunteer)
        volunteer_user_roles = [
            self.volunteer_user.projecttaskrole_set.first(),
            self.scoping_user.projecttaskrole_set.first(),
            self.proj_mgmt_user.projecttaskrole_set.first(),
        ]
        with self.subTest(stage='Volunteer user roles'):
            self.assertEqual(set(ProjectService.get_all_project_volunteers(self.owner_user, self.project.id)), set(volunteer_user_roles))
            self.assertEqual(set(ProjectService.get_project_public_volunteer_list(self.owner_user, self.project.id)), set(volunteer_users))

        scoping_users = [self.scoping_user]
        with self.subTest(stage='Scoping users'):
            test_users_group_inclusion(self, all_users, scoping_users, lambda x: ProjectService.user_is_project_scoper(x, self.project))

        proj_mgmt_users = [self.proj_mgmt_user]
        with self.subTest(stage='Project management users'):
            test_users_group_inclusion(self, all_users, proj_mgmt_users, lambda x: ProjectService.user_is_project_manager(x, self.project))

        volunteer_officials = [self.scoping_user, self.proj_mgmt_user]
        with self.subTest(stage='Volunteer officials'):
            test_users_group_inclusion(self, all_users, volunteer_officials, lambda x: ProjectService.user_is_project_volunteer_official(x, self.project))

        task_editors = [self.owner_user, self.scoping_user]
        with self.subTest(stage='Task editors'):
            test_users_group_inclusion(self, all_users, task_editors, lambda x: ProjectService.user_is_task_editor(x, self.project))

        officials = [self.owner_user, self.scoping_user, self.proj_mgmt_user]
        with self.subTest(stage='Project officials'):
            test_users_group_inclusion(self, all_users, officials, lambda x: ProjectService.user_is_project_official(x, self.project))
            self.assertEqual(set(ProjectService.get_project_officials(self.owner_user, self.project)), set(officials))

        members = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user]
        with self.subTest(stage='Project members'):
            test_users_group_inclusion(self, all_users, members, lambda x: ProjectService.user_is_project_member(x, self.project))
            self.assertEqual(set(ProjectService.get_project_members(self.owner_user, self.project)), set(members))

        commenters = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user]
        with self.subTest(stage='Project commenters'):
            test_users_group_inclusion(self, all_users, commenters, lambda x: ProjectService.user_is_project_commenter(x, self.project))

        # Check that getting project roles from the DB works
        for role in staff_user_roles:
            with self.subTest(stage='Get project roles', role=role):
                self.assertEqual(ProjectService.get_project_role(self.owner_user, self.project.id, role.id), role)

        staff_user_role = self.staff_user.projectrole_set.first()
        owner_user_role = self.owner_user.projectrole_set.first()

        # Check that we can edit the staff member's role
        staff_user_role.role = ProjRole.OWNER
        with self.subTest(stage='Edit project roles'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.scoping_user, self.proj_mgmt_user],
                lambda x: ProjectService.save_project_role(x, self.project.id, staff_user_role))
            ProjectService.save_project_role(self.owner_user, self.project.id, staff_user_role)

        owner_users = [self.owner_user, self.staff_user]
        with self.subTest(stage='Test edited project roles'):
            test_users_group_inclusion(self, all_users, owner_users, lambda x: ProjectService.user_is_project_owner(x, self.project))

        # Check that we can delete the staff member's role
        with self.subTest(stage='Delete project roles'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.scoping_user, self.proj_mgmt_user],
                lambda x: ProjectService.delete_project_role(x, self.project.id, staff_user_role))
            ProjectService.delete_project_role(self.owner_user, self.project.id, staff_user_role)

        owner_users = [self.owner_user]
        with self.subTest(stage='Test deleted project roles'):
            test_users_group_inclusion(self, all_users, owner_users, lambda x: ProjectService.user_is_project_owner(x, self.project))

        # Check that we cannot delete the last owner of a project
        with self.subTest(stage='Prevent deleting last project owner'):
            with self.assertRaisesMessage(ValueError, ''):
                ProjectService.delete_project_role(self.owner_user, self.project.id, owner_user_role)


    def test_project_followers(self):
        OrganizationService.create_project(self.owner_user, self.organization.id, self.project)
        ProjectService.publish_project(self.owner_user, self.project.id, self.project)

        # Check that we can add followers from both staff and the general public
        followers = [self.owner_user, self.volunteer_user]
        with self.subTest(stage='Toggle followers'):
            for user in followers:
                ProjectService.toggle_follower(user, self.project.id)

        # Test that all followers are identified correctly
        all_users = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user]
        with self.subTest(stage='Test followers'):
            test_users_group_inclusion(self, all_users, followers, lambda x: ProjectService.user_is_project_follower(x, self.project))
            self.assertEqual(set(ProjectService.get_project_followers(self.owner_user, self.project.id)), set(followers))
            self.assertEqual(set(ProjectService.get_public_notification_users(self.owner_user, self.project.id)), set(followers))

        with self.subTest(stage='Remove followers'):
            for user in followers:
                ProjectService.toggle_follower(user, self.project.id)
            test_users_group_inclusion(self, all_users, [], lambda x: ProjectService.user_is_project_follower(x, self.project))
            self.assertEqual(set(ProjectService.get_project_followers(self.owner_user, self.project.id)), set([]))

        # Test that the owner user is still in the public notification group
        # even when not being a follower
        with self.subTest(stage='Check public notification group'):
            self.assertEqual(set(ProjectService.get_public_notification_users(self.owner_user, self.project.id)), set([self.owner_user]))


    def test_project_scopes(self):
        self.create_standard_project_structure()

        # Test that the project comes with a scope right after creation
        with self.subTest(stage='Get initial project scopes'):
            all_scopes = ProjectService.get_all_project_scopes(self.owner_user, self.project.id)
            self.assertEqual(len(all_scopes), 1)

        new_scope = ProjectScope()
        new_scope.scope = "New scope."
        new_scope.project_impact = "New project impact."
        new_scope.scoping_process = "New scoping process."
        new_scope.available_staff = "New available staff."
        new_scope.available_data = "New available data."
        new_scope.version_notes = "New version notes."
        new_scope.project = self.project
        new_scope.author = self.owner_user

        # Test that we can update the project scope
        with self.subTest(stage='Update project scope'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user],
                lambda x: ProjectService.update_project_scope(x, self.project.id, new_scope))
            ProjectService.update_project_scope(self.owner_user, self.project.id, new_scope)

        # Test that we can retrieve the new scope
        with self.subTest(stage='Get single project scope'):
            new_scope_saved = ProjectService.get_project_scope(self.owner_user, self.project.id, new_scope.id)
            self.assertEqual(new_scope_saved, new_scope)

        # Test that the current scope returns the latest one
        with self.subTest(stage='Get current project scope'):
            current_scope = ProjectService.get_current_project_scope(self.owner_user, self.project.id)
            self.assertEqual(current_scope, new_scope)

        # Test that we retrieve all project scopes correctly
        with self.subTest(stage='Get all project scopes'):
            all_scopes = ProjectService.get_all_project_scopes(self.owner_user, self.project.id)
            self.assertEqual(len(all_scopes), 2)



    def test_project_channels(self):
        self.create_standard_project_structure()

        all_channels = []
        # Test that the project has the right channels created initially
        with self.subTest(stage='Get initial project discussion channels'):
            all_channels = ProjectService.get_project_channels(self.owner_user, self.project.id)
            self.assertEqual(len(all_channels), 5)

        all_users = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user]
        for channel in all_channels:
            with self.subTest(stage='Test channel operations', channel=channel):
                self.assertEqual(channel, ProjectService.get_project_channel(self.owner_user, self.project, channel.id))
                for user in all_users:
                    if ProjectService.user_is_channel_commenter(user, channel):
                        current_comments = list(ProjectService.get_project_comments(user, channel.id, self.project))
                        comment_text = "C" + str(user.id)
                        comment = ProjectComment()
                        comment.comment = comment_text
                        comment.author = user
                        ProjectService.add_project_comment(user, self.project.id, channel.id, comment)
                        new_comments = ProjectService.get_project_comments(user, channel.id, self.project)
                        self.assertEqual(current_comments, list(new_comments)[1:])
                        self.assertEqual(list(new_comments)[0], comment)
                    else:
                        with self.assertRaisesMessage(PermissionDenied, ''):
                            ProjectService.add_project_comment(user, self.project.id, channel.id, "No comment " + str(user.id))



# ProjectService.get_project_changes(request_user, proj)
# ProjectService.add_project_change(request_user, proj, type, target_type, target_id, description)


# ProjectService.finish_project(request_user, projid, project)
# ProjectService.get_user_projects_with_pending_task_requests(request_user)



    def test_task_operations(self):
        self.create_standard_project_structure()

        task = None
        with self.subTest(stage='Create new task'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user],
                lambda x: ProjectTaskService.create_default_task(x, self.project.id))
            task = ProjectTaskService.create_default_task(self.scoping_user, self.project.id)
            self.assertTrue(task.stage == TaskStatus.DRAFT)
            self.assertTrue(task.accepting_volunteers == False)

        with self.subTest(stage='Edit task'):
            task.name = 'New edited task'
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user],
                lambda x: ProjectTaskService.save_task(x, self.project.id, task.id, task))
            ProjectTaskService.save_task(self.owner_user, self.project.id, task.id, task)
            self.assertEqual(task, ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id))

        application = VolunteerApplication()
        application.volunteer_application_letter = "This is the letter."
        application.task = task
        application.volunteer = self.volunteer_user

        # with self.subTest(stage='Prevent applying to draft tasks'):
        #     with self.assertRaisesMessage(ValueError, ''):
        #         ProjectTaskService.apply_to_volunteer(self.volunteer_user, self.project.id, task.id, application)

        with self.subTest(stage='Publish task'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user],
                lambda x: ProjectTaskService.publish_project_task(x, self.project.id, task.id, task))
            ProjectTaskService.publish_project_task(self.owner_user, self.project.id, task.id, task)
            self.assertTrue(task.stage == TaskStatus.NOT_STARTED)

        if not task:
            task = ProjectTaskService.get_all_tasks(self.owner_user, self.project.id).first()
        initial_accepting_volunteers = task.accepting_volunteers
        with self.subTest(stage='Toggle task accepting volunteers'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user],
                lambda x: ProjectTaskService.toggle_task_accepting_volunteers(x, self.project.id, task.id))
            ProjectTaskService.toggle_task_accepting_volunteers(self.owner_user, self.project.id, task.id)
            self.assertTrue(initial_accepting_volunteers != ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id).accepting_volunteers)
            ProjectTaskService.toggle_task_accepting_volunteers(self.owner_user, self.project.id, task.id)
            self.assertTrue(initial_accepting_volunteers == ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id).accepting_volunteers)

        with self.subTest(stage='Apply to task'):
            ProjectTaskService.apply_to_volunteer(self.volunteer_user, self.project.id, task.id, application)

        # with self.subTest(stage='Prevent applying twice to the same task'):
        #     with self.assertRaisesMessage(ValueError, ''):
        #         ProjectTaskService.apply_to_volunteer(self.volunteer_user, self.project.id, task.id, application)

        with self.subTest(stage='Prevent applying to task without volunteer profile'):
            with self.assertRaisesMessage(PermissionDenied, ''):
                application.volunteer = self.owner_user
                ProjectTaskService.apply_to_volunteer(self.owner_user, self.project.id, task.id, application)

#
# check the all the paths within ProjectTaskService.save_task_internal(request_user, projid, taskid, project_task) ??
#
# ProjectTaskService.delete_task(request_user, projid, project_task)

#
#
# ProjectTaskService.apply_to_volunteer(request_user, projid, taskid, task_application_request)
# ProjectTaskService.get_volunteer_application(request_user, projid, taskid, volunteer_application_pk)
# ProjectTaskService.save_volunteer_application(request_user, projid, taskid, volunteer_application) ??
# ProjectTaskService.accept_volunteer(request_user, projid, taskid, volunteer_application)
# ProjectTaskService.reject_volunteer(request_user, projid, taskid, volunteer_application)
#
#
# ProjectTaskService.mark_task_as_completed(request_user, projid, taskid, project_task_review)
# ProjectTaskService.get_project_task_review(request_user, projid, taskid, reviewid)
# ProjectTaskService.save_task_review(request_user, projid, taskid, task_review) ??
# ProjectTaskService.update_user_badge(request_user, badge_type, badge_tier, badge_name) ??
# ProjectTaskService.update_user_task_count(request_user) ??
# ProjectTaskService.update_user_review_score(request_user) ??
# ProjectTaskService.update_user_work_speed(request_user) ??
# ProjectTaskService.accept_task_review(request_user, projid, taskid, task_review)
# ProjectTaskService.reject_task_review(request_user, projid, taskid, task_review)
# ProjectTaskService.get_task_reviews(request_user, project_task, expand_pinned=False)
# ProjectTaskService.user_belongs_to_task_review(request_user, task_review)
# ProjectTaskService.toggle_pinned_task_review(request_user, projid, taskid, task_reviewid)
#
# ProjectTaskService.get_project_task(request_user, projid, taskid)
# ProjectTaskService.get_all_tasks(request_user, proj)
# ProjectTaskService.get_open_tasks(request_user, proj)
# ProjectTaskService.get_public_tasks(request_user, proj)
# ProjectTaskService.get_project_tasks_summary(request_user, proj)
# ProjectTaskService.get_non_finished_tasks(request_user, proj)
# ProjectTaskService.get_volunteer_current_tasks(request_user, volunteer, projid)
# ProjectTaskService.get_volunteer_task_applications(request_user, projid)
# ProjectTaskService.get_volunteer_all_tasks(request_user, target_user)
# ProjectTaskService.get_volunteer_all_project_tasks(request_user, target_user, project)
# ProjectTaskService.get_user_in_progress_tasks(request_user)
#
# ProjectTaskService.user_is_task_volunteer(user, task)
# ProjectTaskService.user_can_view_volunteer_application(user, volunteer_application)
# ProjectTaskService.user_can_review_task(user, task)
# ProjectTaskService.task_has_volunteers(request_user, taskid)
# ProjectTaskService.get_task_volunteers(request_user, taskid)
#
# ProjectTaskService.cancel_volunteering(request_user, projid, taskid, project_task_role)
#
# ProjectTaskService.get_task_staff(request_user, taskid)
# ProjectTaskService.get_project_task_staff_for_editing(request_user, projid, taskid)
# ProjectTaskService.set_task_staff(request_user, projid, taskid, post_object)
#
#
# ProjectTaskService.get_project_taks_requirement_importance_levels()
# ProjectTaskService.get_project_task_requirements(request_user, projid, taskid)
# ProjectTaskService.set_task_requirements(request_user, projid, taskid, post_object)
#
# ProjectTaskService.get_project_task_role(request_user, projid, taskid, roleid)
# ProjectTaskService.get_own_project_task_role(request_user, projid, taskid)
# ProjectTaskService.save_project_task_role(request_user, projid, taskid, project_task_role)
# ProjectTaskService.delete_project_task_role(request_user, projid, taskid, project_task_role)
