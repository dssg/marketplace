from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

from dssgmkt.models.common import ReviewStatus
from dssgmkt.models.proj import ProjectRole, ProjRole, TaskType, VolunteerApplication, ProjectScope
from dssgmkt.models.user import SignupCodeType, SignupCode
from dssgmkt.domain.user import UserService
from dssgmkt.domain.org import OrganizationService
from dssgmkt.domain.proj import ProjectService, ProjectTaskService

from dssgmkt.tests.domain.common import example_organization_user, example_staff_user, example_volunteer_user, example_organization, example_project

def test_users_group_inclusion(test_case, all_users, included_users, predicate):
    for user in all_users:
        # print("User ", user, " is ", user in included_users, " test: ", predicate(user))
        test_case.assertEqual(predicate(user), user in included_users)

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

        with self.assertRaisesMessage(PermissionDenied, ''):
            OrganizationService.create_project(AnonymousUser(), self.organization.id, self.project)
        with self.assertRaisesMessage(PermissionDenied, ''):
            OrganizationService.create_project(self.volunteer_user, self.organization.id, self.project)
        with self.assertRaisesMessage(PermissionDenied, ''):
            OrganizationService.create_project(self.staff_user, self.organization.id, self.project)
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

        self.project.name = "EDITED demo project 1"
        with self.assertRaisesMessage(PermissionDenied, ''):
            ProjectService.save_project(AnonymousUser(), self.project.id, self.project)
        with self.assertRaisesMessage(PermissionDenied, ''):
            ProjectService.save_project(self.volunteer_user, self.project.id, self.project)
        ProjectService.save_project(self.owner_user, self.project.id, self.project)
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id), self.project)

        with self.assertRaisesMessage(PermissionDenied, ''):
            ProjectService.publish_project(self.volunteer_user, self.project.id, self.project)
        with self.assertRaisesMessage(PermissionDenied, ''):
            ProjectService.publish_project(AnonymousUser(), self.project.id, self.project)
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
        with self.assertRaisesMessage(PermissionDenied, ''):
            ProjectService.add_staff_member(self.staff_user, self.project.id, staff_user_role)
        with self.assertRaisesMessage(PermissionDenied, ''):
            ProjectService.add_staff_member(self.volunteer_user, self.project.id, staff_user_role)
        with self.assertRaisesMessage(PermissionDenied, ''):
            ProjectService.add_staff_member(AnonymousUser(), self.project.id, staff_user_role)
        ProjectService.add_staff_member(self.owner_user, self.project.id, staff_user_role)

        tasks = ProjectTaskService.get_all_tasks(self.owner_user, self.project)
        scoping_task = None
        project_management_task = None
        domain_work_task = None
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

    def test_project_roles(self):
        self.create_standard_project_structure()

        all_users = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user]
        self.assertEqual(set(ProjectService.get_all_project_users(self.owner_user, self.project)), set(all_users))
        self.assertEqual(set(ProjectService.get_public_notification_users(self.owner_user, self.project)), set(all_users))

        owner_users = [self.owner_user]
        test_users_group_inclusion(self, all_users, owner_users, lambda x: ProjectService.user_is_project_owner(x, self.project))

        owner_user_roles = [self.owner_user.projectrole_set.first()]
        self.assertEqual(set(ProjectService.get_project_owners(self.owner_user, self.project.id)), set(owner_user_roles))

        staff_user_roles = [self.owner_user.projectrole_set.first(), self.staff_user.projectrole_set.first()]
        self.assertEqual(set(ProjectService.get_all_project_staff(self.owner_user, self.project.id)), set(staff_user_roles))

        volunteer_users = [self.scoping_user, self.proj_mgmt_user, self.volunteer_user]
        test_users_group_inclusion(self, all_users, volunteer_users, lambda x: ProjectService.user_is_project_volunteer(x, self.project))
        test_users_group_inclusion(self, all_users, volunteer_users, ProjectService.user_is_volunteer)
        volunteer_user_roles = [
            self.volunteer_user.projecttaskrole_set.first(),
            self.scoping_user.projecttaskrole_set.first(),
            self.proj_mgmt_user.projecttaskrole_set.first(),
        ]
        self.assertEqual(set(ProjectService.get_all_project_volunteers(self.owner_user, self.project.id)), set(volunteer_user_roles))
        self.assertEqual(set(ProjectService.get_project_public_volunteer_list(self.owner_user, self.project.id)), set(volunteer_users))

        scoping_users = [self.scoping_user]
        test_users_group_inclusion(self, all_users, scoping_users, lambda x: ProjectService.user_is_project_scoper(x, self.project))

        proj_mgmt_users = [self.proj_mgmt_user]
        test_users_group_inclusion(self, all_users, proj_mgmt_users, lambda x: ProjectService.user_is_project_manager(x, self.project))

        volunteer_officials = [self.scoping_user, self.proj_mgmt_user]
        test_users_group_inclusion(self, all_users, volunteer_officials, lambda x: ProjectService.user_is_project_volunteer_official(x, self.project))

        task_editors = [self.owner_user, self.scoping_user]
        test_users_group_inclusion(self, all_users, task_editors, lambda x: ProjectService.user_is_task_editor(x, self.project))

        officials = [self.owner_user, self.scoping_user, self.proj_mgmt_user]
        test_users_group_inclusion(self, all_users, officials, lambda x: ProjectService.user_is_project_official(x, self.project))
        self.assertEqual(set(ProjectService.get_project_officials(self.owner_user, self.project)), set(officials))

        members = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user]
        test_users_group_inclusion(self, all_users, members, lambda x: ProjectService.user_is_project_member(x, self.project))
        self.assertEqual(set(ProjectService.get_project_members(self.owner_user, self.project)), set(members))

        commenters = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user]
        test_users_group_inclusion(self, all_users, commenters, lambda x: ProjectService.user_is_project_commenter(x, self.project))



    def test_project_followers(self):
        OrganizationService.create_project(self.owner_user, self.organization.id, self.project)
        ProjectService.publish_project(self.owner_user, self.project.id, self.project)
        followers = [self.owner_user, self.volunteer_user]
        for user in followers:
            ProjectService.toggle_follower(user, self.project.id)

        all_users = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user]
        test_users_group_inclusion(self, all_users, followers, lambda x: ProjectService.user_is_project_follower(x, self.project))
        self.assertEqual(set(ProjectService.get_project_followers(self.owner_user, self.project.id)), set(followers))
        self.assertEqual(set(ProjectService.get_public_notification_users(self.owner_user, self.project.id)), set(followers))

        for user in followers:
            ProjectService.toggle_follower(user, self.project.id)
        test_users_group_inclusion(self, all_users, [], lambda x: ProjectService.user_is_project_follower(x, self.project))
        self.assertEqual(set(ProjectService.get_project_followers(self.owner_user, self.project.id)), set([]))

        self.assertEqual(set(ProjectService.get_public_notification_users(self.owner_user, self.project.id)), set([self.owner_user]))


    def test_project_scopes(self):
        self.create_standard_project_structure()
        new_scope = ProjectScope()
        new_scope.scope = "New scope."
        new_scope.project_impact = "New project impact."
        new_scope.scoping_process = "New scoping process."
        new_scope.available_staff = "New available staff."
        new_scope.available_data = "New available data."
        new_scope.version_notes = "New version notes."
        new_scope.project = self.project
        new_scope.author = self.owner_user
        ProjectService.update_project_scope(self.owner_user, self.project.id, new_scope)
        new_scope_saved = ProjectService.get_project_scope(self.owner_user, self.project.id, new_scope.id)
        self.assertEqual(new_scope_saved, new_scope)

        current_scope = ProjectService.get_current_project_scope(self.owner_user, self.project.id)
        self.assertEqual(current_scope, new_scope)

        all_scopes = ProjectService.get_all_project_scopes(self.owner_user, self.project.id)
        self.assertEqual(len(all_scopes), 2)

# ProjectService.get_all_project_scopes(request_user, projid)
# ProjectService.get_current_project_scope(request_user, projid)
# ProjectService.get_project_scope(request_user, projid, scopeid)
# ProjectService.update_project_scope(request_user, projid, project_scope)

# ProjectService.get_project_role(request_user, projid, roleid)


# ProjectService.get_all_volunteer_applications(request_user, projid)

# ProjectService.save_project_role(request_user, projid, project_role)
# ProjectService.delete_project_role(request_user, projid, project_role)


# ProjectService.get_project_changes(request_user, proj)
# ProjectService.get_project_channels(request_user, proj)
# ProjectService.get_project_channel(request_user, proj, channelid)
# ProjectService.get_project_comments(request_user, channelid, proj)
# ProjectService.add_project_change(request_user, proj, type, target_type, target_id, description)
# ProjectService.add_project_comment(request_user, projid, channelid, project_comment)
# ProjectService.user_is_channel_commenter(user, channel)


# ProjectService.finish_project(request_user, projid, project)
# ProjectService.get_user_projects_with_pending_task_requests(request_user)
