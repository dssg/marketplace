from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

from marketplace.domain import marketplace
from marketplace.domain.org import OrganizationService
from marketplace.domain.proj import ProjectService, ProjectTaskService

from marketplace.models.common import ReviewStatus, SkillLevel, Score, TaskType
from marketplace.models.proj import (
    ProjectRole, ProjRole, VolunteerApplication, ProjectScope,
    TaskStatus, ProjectComment, ProjectTaskRole, ProjectTaskReview,
    ProjectStatus, TaskRequirementImportance, ProjectTaskRequirement,
)
from marketplace.models.user import SignupCodeType, SignupCode, Skill

from marketplace.tests.domain.common import (
    example_organization_user, example_staff_user, example_volunteer_user,
    example_organization, example_project,
    test_users_group_inclusion, test_permission_denied_operation,
)


class ProjectTestCase(TestCase):

    owner_user = None
    staff_user = None
    volunteer_user = None
    volunteer_applicant_user = None
    scoping_user = None
    proj_mgmt_user = None
    qa_user = None
    organization = None
    project = None

    def setUp(self):
        code = SignupCode()
        code.name = "AUTOMATICVOLUNTEER"
        code.type = SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT
        code.save()

        self.owner_user = example_organization_user()
        marketplace.user.add_user(self.owner_user, 'organization')

        self.staff_user = example_staff_user()
        marketplace.user.add_user(self.staff_user, 'organization')

        self.volunteer_user = example_volunteer_user()
        self.volunteer_user.special_code = "AUTOMATICVOLUNTEER"
        marketplace.user.add_user(self.volunteer_user, 'volunteer')

        self.volunteer_applicant_user = example_volunteer_user(
            username="applicant",
            email='applicant-volunteer@example.com',
            special_code="AUTOMATICVOLUNTEER",
        )
        marketplace.user.add_user(self.volunteer_applicant_user, 'volunteer')

        self.scoping_user = example_volunteer_user(
            username="scopinguser",
            email='scopinguser@example.com',
            special_code="AUTOMATICVOLUNTEER",
        )
        marketplace.user.add_user(self.scoping_user, 'volunteer')

        self.proj_mgmt_user = example_volunteer_user(
            username="managementuser",
            email='managementuser@example.com',
            special_code="AUTOMATICVOLUNTEER",
        )
        marketplace.user.add_user(self.proj_mgmt_user, 'volunteer')

        self.qa_user = example_volunteer_user(
            username="qauser",
            email="qa@email.com",
            special_code="AUTOMATICVOLUNTEER",
        )
        marketplace.user.add_user(self.qa_user, 'volunteer')

        self.organization = example_organization()
        OrganizationService.create_organization(self.owner_user, self.organization)
        OrganizationService.add_staff_member_by_id(self.owner_user, self.organization.id, self.staff_user.id, None)

        self.project = example_project()

    def test_create_project(self):
        self.assertEqual(list(marketplace.project.list_public_projects()), [])
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
        self.assertEqual(list(marketplace.project.list_public_projects()), [])
        self.assertEqual(list(ProjectService.get_all_organization_projects(self.owner_user, self.organization)), projects_list)
        self.assertEqual(list(ProjectService.get_organization_public_projects(self.owner_user, self.organization)), [])
        self.assertEqual(ProjectService.get_featured_project(), None)
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id), self.project)
        self.assertTrue(marketplace.project.user.can_view(self.owner_user, self.project))
        self.assertFalse(marketplace.project.user.can_view(self.staff_user, self.project))
        self.assertFalse(marketplace.project.user.can_view(self.volunteer_user, self.project))
        self.assertFalse(marketplace.project.user.can_view(AnonymousUser(), self.project))
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

        self.assertEqual(list(marketplace.project.list_public_projects()), [self.project])
        self.assertEqual(list(ProjectService.get_all_organization_projects(self.owner_user, self.organization)), projects_list)
        self.assertEqual(list(ProjectService.get_organization_public_projects(self.owner_user, self.organization)), projects_list)
        self.assertEqual(ProjectService.get_featured_project(), self.project)
        self.assertEqual(list(ProjectService.get_user_projects_in_draft_status(self.owner_user)), [])

    def create_standard_project_structure(self, publish_project=True, accept_volunteers=True):
        OrganizationService.create_project(self.owner_user, self.organization.id, self.project)
        if publish_project:
            ProjectService.publish_project(self.owner_user, self.project.id, self.project)
        staff_user_role = ProjectRole()
        staff_user_role.user = self.staff_user
        staff_user_role.project = self.project
        staff_user_role.role = ProjRole.STAFF

        # Test adding staff members
        test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user],
            lambda x: ProjectService.add_staff_member(x, self.project.id, staff_user_role))
        ProjectService.add_staff_member(self.owner_user, self.project.id, staff_user_role)

        scoping_task = None
        project_management_task = None
        domain_work_task = None
        qa_task = None
        # For each task of the project, we 1) make it public, 2) allow volunteers
        # to apply, 3) apply to it with a volunteer user, and 4) accept the
        # volunteer application. Each task gets a different user so we can test
        # their permissions appropriately later.
        tasks = ProjectTaskService.get_all_tasks(self.owner_user, self.project)
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
            elif task.type == TaskType.QA_TASK:
                qa_task = task
                application.volunteer = self.qa_user
            ProjectTaskService.apply_to_volunteer(application.volunteer, self.project.id, task.id, application)
            self.assertEqual(list(ProjectService.get_user_projects_with_pending_volunteer_requests(self.owner_user)), [self.project])
            if accept_volunteers:
                ProjectTaskService.accept_volunteer(self.owner_user, self.project.id, task.id, application)
                self.assertEqual(list(ProjectService.get_user_projects_with_pending_volunteer_requests(self.owner_user)), [])
            volunteer_applications.append(application)
        self.assertEqual(set(ProjectService.get_all_volunteer_applications(self.owner_user, self.project.id)), set(volunteer_applications))
        return (scoping_task, project_management_task, domain_work_task, qa_task)

    def get_all_users(self):
        return [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user, self.volunteer_applicant_user, self.qa_user]

    def test_project_roles(self):
        self.create_standard_project_structure()

        # Check the membership of users to the various user groups that exist in projects
        all_users = self.get_all_users()
        project_users = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user, self.qa_user]
        self.assertEqual(set(ProjectService.get_all_project_users(self.owner_user, self.project)), set(project_users))
        self.assertEqual(set(marketplace.project.query_notification_users(self.project)), set(project_users))

        owner_users = [self.owner_user]
        with self.subTest(stage='Owner users'):
            test_users_group_inclusion(self, all_users, owner_users, lambda x: marketplace.project.user.is_owner(x, self.project))

        owner_user_roles = [self.owner_user.projectrole_set.first()]
        with self.subTest(stage='Owner user roles'):
            self.assertEqual(set(ProjectService.get_project_owners(self.owner_user, self.project.id)), set(owner_user_roles))

        staff_user_roles = [self.owner_user.projectrole_set.first(), self.staff_user.projectrole_set.first()]
        with self.subTest(stage='Staff user roles'):
            self.assertEqual(set(ProjectService.get_all_project_staff(self.owner_user, self.project.id)), set(staff_user_roles))

        volunteer_users = [self.scoping_user, self.proj_mgmt_user, self.volunteer_user, self.qa_user]
        with self.subTest(stage='Volunteer users'):
            test_users_group_inclusion(self, all_users, volunteer_users, lambda x: marketplace.project.user.is_volunteer(x, self.project))
            test_users_group_inclusion(self, all_users, volunteer_users, marketplace.project.user.is_active)
        volunteer_user_roles = [
            self.volunteer_user.projecttaskrole_set.first(),
            self.scoping_user.projecttaskrole_set.first(),
            self.proj_mgmt_user.projecttaskrole_set.first(),
            self.qa_user.projecttaskrole_set.first(),
        ]
        with self.subTest(stage='Volunteer user roles'):
            self.assertEqual(set(ProjectService.get_all_project_volunteers(self.owner_user, self.project.id)), set(volunteer_user_roles))
            self.assertEqual(set(ProjectService.get_project_public_volunteer_list(self.owner_user, self.project.id)), set(volunteer_users))

        scoping_users = [self.scoping_user]
        with self.subTest(stage='Scoping users'):
            test_users_group_inclusion(self, all_users, scoping_users, lambda x: marketplace.project.user.is_scoper(x, self.project))

        proj_mgmt_users = [self.proj_mgmt_user]
        with self.subTest(stage='Project management users'):
            test_users_group_inclusion(self, all_users, proj_mgmt_users, lambda x: marketplace.project.user.is_manager(x, self.project))

        volunteer_officials = [self.scoping_user, self.proj_mgmt_user]
        with self.subTest(stage='Volunteer officials'):
            test_users_group_inclusion(self, all_users, volunteer_officials, lambda x: marketplace.project.user.is_volunteer_official(x, self.project))

        task_editors = [self.owner_user, self.scoping_user]
        with self.subTest(stage='Task editors'):
            test_users_group_inclusion(self, all_users, task_editors, lambda x: marketplace.project.user.is_task_editor(x, self.project))

        officials = [self.owner_user, self.scoping_user, self.proj_mgmt_user]
        with self.subTest(stage='Project officials'):
            test_users_group_inclusion(self, all_users, officials, lambda x: marketplace.project.user.is_official(x, self.project))
            self.assertEqual(set(ProjectService.get_project_officials(self.owner_user, self.project)), set(officials))

        members = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user]
        with self.subTest(stage='Project members'):
            test_users_group_inclusion(self, all_users, members, lambda x: marketplace.project.user.is_member(x, self.project))
            self.assertEqual(set(ProjectService.get_project_members(self.owner_user, self.project)), set(members))

        commenters = [self.owner_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_user, self.qa_user]
        with self.subTest(stage='Project commenters'):
            test_users_group_inclusion(self, all_users, commenters, lambda x: marketplace.project.user.is_commenter(x, self.project))

        reviewers = [self.qa_user]
        with self.subTest(stage='Project reviewers'):
            test_users_group_inclusion(self, all_users, reviewers, lambda x: marketplace.project.user.is_reviewer(x, self.project))

        # Check that getting project roles from the DB works
        for role in staff_user_roles:
            with self.subTest(stage='Get project roles', role=role):
                self.assertEqual(ProjectService.get_project_role(self.owner_user, self.project.id, role.id), role)

        staff_user_role = self.staff_user.projectrole_set.first()
        owner_user_role = self.owner_user.projectrole_set.first()

        # Check that we can edit the staff member's role
        staff_user_role.role = ProjRole.OWNER
        with self.subTest(stage='Edit project roles'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.scoping_user, self.proj_mgmt_user, self.qa_user],
                lambda x: ProjectService.save_project_role(x, self.project.id, staff_user_role))
            ProjectService.save_project_role(self.owner_user, self.project.id, staff_user_role)

        owner_users = [self.owner_user, self.staff_user]
        with self.subTest(stage='Test edited project roles'):
            test_users_group_inclusion(self, all_users, owner_users, lambda x: marketplace.project.user.is_owner(x, self.project))

        # Check that we can delete the staff member's role
        with self.subTest(stage='Delete project roles'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.scoping_user, self.proj_mgmt_user, self.qa_user],
                lambda x: ProjectService.delete_project_role(x, self.project.id, staff_user_role))
            ProjectService.delete_project_role(self.owner_user, self.project.id, staff_user_role)

        owner_users = [self.owner_user]
        with self.subTest(stage='Test deleted project roles'):
            test_users_group_inclusion(self, all_users, owner_users, lambda x: marketplace.project.user.is_owner(x, self.project))

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
        all_users = self.get_all_users()
        with self.subTest(stage='Test followers'):
            test_users_group_inclusion(self, all_users, followers, lambda x: marketplace.project.user.is_follower(x, self.project))
            self.assertEqual(set(ProjectService.get_project_followers(self.owner_user, self.project.id)), set(followers))
            self.assertEqual(set(marketplace.project.query_notification_users(self.project.id)), set(followers))

        with self.subTest(stage='Remove followers'):
            for user in followers:
                ProjectService.toggle_follower(user, self.project.id)
            test_users_group_inclusion(self, all_users, [], lambda x: marketplace.project.user.is_follower(x, self.project))
            self.assertEqual(set(ProjectService.get_project_followers(self.owner_user, self.project.id)), set([]))

        # Test that the owner user is still in the public notification group
        # even when not being a follower
        with self.subTest(stage='Check public notification group'):
            self.assertEqual(set(marketplace.project.query_notification_users(self.project.id)), set([self.owner_user]))


    def test_project_scopes(self):
        self.create_standard_project_structure()

        # Test that the project comes with a scope right after creation
        with self.subTest(stage='Get initial project scopes'):
            all_scopes = ProjectService.get_all_project_scopes(self.owner_user, self.project.id)
            self.assertEqual(len(all_scopes), 1)

        new_scope = ProjectScope()
        new_scope.scope_goals = 'New goals'
        new_scope.scope_interventions = 'New interventions'
        new_scope.scope_available_data = 'New data'
        new_scope.scope_analysis = 'New analysis'
        new_scope.scope_validation_methodology = 'New validation methodology'
        new_scope.scope_implementation = 'New implementation plan'
        new_scope.version_notes = "New version notes."
        new_scope.project = self.project
        new_scope.author = self.owner_user

        # Test that we can update the project scope
        with self.subTest(stage='Update project scope'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.qa_user],
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
            self.assertEqual(len(all_channels), 6)

        all_users = self.get_all_users()
        for channel in all_channels:
            with self.subTest(stage='Test channel operations', channel=channel):
                self.assertEqual(channel, ProjectService.get_project_channel(self.owner_user, self.project, channel.id))
                for user in all_users:
                    if marketplace.project.user.is_channel_commenter(user, channel):
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



    def test_task_operations(self):
        scoping_task, project_management_task, domain_work_task, qa_task = self.create_standard_project_structure()
        all_users = self.get_all_users()

        task = None
        with self.subTest(stage='Create new task'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.qa_user],
                lambda x: ProjectTaskService.create_default_task(x, self.project.id))
            task = ProjectTaskService.create_default_task(self.scoping_user, self.project.id)
            self.assertTrue(task.stage == TaskStatus.DRAFT)
            self.assertTrue(task.accepting_volunteers == False)
            self.assertEqual(set(ProjectTaskService.get_open_tasks(self.owner_user, self.project.id)),
                set([scoping_task, project_management_task, domain_work_task, qa_task]))

        with self.subTest(stage='Edit task'):
            task.name = 'New edited task'
            task.type = TaskType.DOMAIN_WORK_TASK
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.qa_user],
                lambda x: ProjectTaskService.save_task(x, self.project.id, task.id, task))
            ProjectTaskService.save_task(self.owner_user, self.project.id, task.id, task)
            self.assertEqual(task, ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id))

        application = VolunteerApplication()
        application.volunteer_application_letter = "This is the letter."
        application.task = task
        application.volunteer = self.volunteer_applicant_user

        ## TODO This check is not currently implemented in the domain logic layer
        # with self.subTest(stage='Prevent applying to draft tasks'):
        #     with self.assertRaisesMessage(ValueError, ''):
        #         ProjectTaskService.apply_to_volunteer(self.volunteer_user, self.project.id, task.id, application)

        with self.subTest(stage='Publish task'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.qa_user],
                lambda x: ProjectTaskService.publish_project_task(x, self.project.id, task.id, task))
            ProjectTaskService.publish_project_task(self.owner_user, self.project.id, task.id, task)
            self.assertTrue(task.stage == TaskStatus.NOT_STARTED)

        if not task:
            task = ProjectTaskService.get_all_tasks(self.owner_user, self.project.id).first()
        initial_accepting_volunteers = task.accepting_volunteers
        with self.subTest(stage='Toggle task accepting volunteers'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.qa_user],
                lambda x: ProjectTaskService.toggle_task_accepting_volunteers(x, self.project.id, task.id))
            ProjectTaskService.toggle_task_accepting_volunteers(self.owner_user, self.project.id, task.id)
            self.assertTrue(initial_accepting_volunteers != ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id).accepting_volunteers)
            ProjectTaskService.toggle_task_accepting_volunteers(self.owner_user, self.project.id, task.id)
            self.assertTrue(initial_accepting_volunteers == ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id).accepting_volunteers)


        with self.subTest(stage='Get task volunteers with no volunteers'):
            self.assertFalse(ProjectTaskService.task_has_volunteers(self.owner_user, task.id))
            self.assertEqual(list(ProjectTaskService.get_task_volunteers(self.owner_user, task.id)), [])

        with self.subTest(stage='Apply to task'):
            ProjectTaskService.apply_to_volunteer(self.volunteer_applicant_user, self.project.id, task.id, application)

        # with self.subTest(stage='Prevent applying twice to the same task'):
        #     with self.assertRaisesMessage(ValueError, ''):
        #         ProjectTaskService.apply_to_volunteer(self.volunteer_user, self.project.id, task.id, application)

        with self.subTest(stage='Get volunteer applications'):
            all_applications = ProjectService.get_all_volunteer_applications(self.owner_user, self.project.id)
            self.assertEqual(len(all_applications), 5)
            open_applications = [x for x in all_applications if x.status == ReviewStatus.NEW]
            self.assertEqual(open_applications, [application])
            test_permission_denied_operation(self, [AnonymousUser(), self.staff_user, self.volunteer_user, self.qa_user],
                lambda x: ProjectTaskService.get_volunteer_application(x, self.project.id, task.id, application.id))
            self.assertEqual(set(ProjectTaskService.get_volunteer_open_task_applications(self.volunteer_applicant_user, self.project.id)), set([application]))

            viewers = [self.owner_user, self.scoping_user, self.proj_mgmt_user, self.volunteer_applicant_user]
            with self.subTest(stage='Volunteer application viewers'):
                test_users_group_inclusion(self, all_users, viewers, lambda x: ProjectTaskService.user_can_view_volunteer_application(x, application))


        with self.subTest(stage='Get task volunteers with applications'):
            self.assertFalse(ProjectTaskService.task_has_volunteers(self.owner_user, task.id))
            self.assertEqual(list(ProjectTaskService.get_task_volunteers(self.owner_user, task.id)), [])

        with self.subTest(stage='Reject volunteer application'):
            test_permission_denied_operation(self, [AnonymousUser(), self.staff_user, self.volunteer_user, self.volunteer_applicant_user, self.qa_user],
                lambda x: ProjectTaskService.reject_volunteer(x, self.project.id, task.id, ProjectTaskService.get_volunteer_application(self.owner_user, self.project.id, task.id, application.id)))
            application = ProjectTaskService.get_volunteer_application(self.owner_user, self.project.id, task.id, application.id)
            ProjectTaskService.reject_volunteer(self.scoping_user, self.project.id, task.id, application)
            saved_application = ProjectTaskService.get_volunteer_application(self.owner_user, self.project.id, task.id, application.id)
            self.assertEqual(saved_application.status, ReviewStatus.REJECTED)
            self.assertFalse(marketplace.project.user.is_volunteer(self.volunteer_applicant_user, self.project))
            self.assertFalse(ProjectTaskService.user_is_task_volunteer(self.volunteer_applicant_user, task))

        with self.subTest(stage='Accept volunteer application'):
            application.id = None
            ProjectTaskService.apply_to_volunteer(self.volunteer_applicant_user, self.project.id, task.id, application)
            test_permission_denied_operation(self, [AnonymousUser(), self.staff_user, self.volunteer_user, self.volunteer_applicant_user, self.qa_user],
                lambda x: ProjectTaskService.accept_volunteer(x, self.project.id, task.id, ProjectTaskService.get_volunteer_application(self.owner_user, self.project.id, task.id, application.id)))
            application = ProjectTaskService.get_volunteer_application(self.owner_user, self.project.id, task.id, application.id)
            ProjectTaskService.accept_volunteer(self.scoping_user, self.project.id, task.id, application)
            saved_application = ProjectTaskService.get_volunteer_application(self.owner_user, self.project.id, task.id, application.id)
            self.assertEqual(saved_application.status, ReviewStatus.ACCEPTED)
            self.assertTrue(ProjectTaskService.user_is_task_volunteer(self.volunteer_applicant_user, task))

        with self.subTest(stage='Get task volunteers'):
            self.assertTrue(ProjectTaskService.task_has_volunteers(self.owner_user, task.id))
            self.assertEqual(list(ProjectTaskService.get_task_volunteers(self.owner_user, task.id)), [self.volunteer_applicant_user])

        with self.subTest(stage='Prevent applying to task without volunteer profile'):
            with self.assertRaisesMessage(PermissionDenied, ''):
                application.volunteer = self.owner_user
                ProjectTaskService.apply_to_volunteer(self.owner_user, self.project.id, task.id, application)

        with self.subTest(stage='Prevent deleting task with volunteers'):
            with self.assertRaisesMessage(ValueError, ''):
                ProjectTaskService.delete_task(self.owner_user, self.project.id, task)


        with self.subTest(stage='Complete task'):
            task_review = ProjectTaskReview()
            task_review.volunteer_comment = "Completed."
            task_review.volunteer_effort_hours = 1
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.scoping_user, self.owner_user, self.qa_user],
                lambda x: ProjectTaskService.mark_task_as_completed(x, self.project.id, task.id, task_review))
            ProjectTaskService.mark_task_as_completed(self.volunteer_applicant_user, self.project.id, task.id, task_review)
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user],
                lambda x: ProjectTaskService.get_project_task_review(x, self.project.id, task.id, task_review.id))
            self.assertEqual(ProjectTaskService.get_project_task_review(self.owner_user,
                self.project.id, task.id, task_review.id).review_result, ReviewStatus.NEW)
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user],
                lambda x: ProjectTaskService.get_task_reviews(x, task))
            task_reviews = ProjectTaskService.get_task_reviews(self.owner_user, task)
            self.assertEqual(len(task_reviews), 1)
            self.assertEqual(task_reviews[0], task_review)
            self.assertEqual(ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id).stage, TaskStatus.WAITING_REVIEW)
            with self.subTest(stage='Volunteer belongs to task review'):
                test_users_group_inclusion(self, all_users, [self.volunteer_applicant_user],
                    lambda x: ProjectTaskService.user_belongs_to_task_review(x, task_review))

        with self.subTest(stage='User can review task'):
            test_users_group_inclusion(self, all_users, [self.owner_user, self.qa_user],
                lambda x: ProjectTaskService.user_can_review_task(x, task))

        with self.subTest(stage='Projects with pending reviews'):
            for user in [self.owner_user, self.scoping_user, self.proj_mgmt_user]:
                with self.subTest(user=user):
                    self.assertEqual(set(ProjectService.get_user_projects_with_pending_task_requests(user)), set([self.project]))
            for user in [AnonymousUser(), self.volunteer_user, self.volunteer_applicant_user]:
                with self.subTest(user=user):
                    self.assertEqual(set(ProjectService.get_user_projects_with_pending_task_requests(user)), set([]))

        with self.subTest(stage='Task getters 1'):
            self.assertEqual(task, ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id))
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user],
                lambda x: ProjectTaskService.get_all_tasks(x, self.project))
            self.assertEqual(set(self.project.projecttask_set.all()), set(ProjectTaskService.get_all_tasks(self.owner_user, self.project)))

            self.assertEqual(set(ProjectTaskService.get_public_tasks(self.owner_user, self.project.id)),
                set([scoping_task, project_management_task, domain_work_task, qa_task, task]))
            self.assertEqual(set(ProjectTaskService.get_project_tasks_summary(self.owner_user, self.project.id)),
                set([scoping_task, project_management_task, domain_work_task, qa_task, task]))
            self.assertEqual(set(ProjectTaskService.get_non_finished_tasks(self.owner_user, self.project.id)),
                set([scoping_task, project_management_task, domain_work_task, qa_task, task]))

            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.scoping_user, self.owner_user, self.qa_user],
                lambda x: ProjectTaskService.get_volunteer_current_tasks(x, self.volunteer_applicant_user, self.project.id))
            self.assertEqual(set(ProjectTaskService.get_volunteer_current_tasks(self.volunteer_applicant_user, self.volunteer_applicant_user, self.project.id)),
                set([task]))
            self.assertEqual(set(ProjectTaskService.get_volunteer_all_project_tasks(self.volunteer_applicant_user, self.volunteer_applicant_user, self.project)),
                set([task]))
            self.assertEqual(set(ProjectTaskService.get_volunteer_all_tasks(self.owner_user, self.volunteer_applicant_user)),
                set([task]))
            self.assertEqual(set(ProjectTaskService.get_user_in_progress_tasks(self.volunteer_applicant_user)),
                set([task]))


        with self.subTest(stage='Reject task review'):
            task_review = ProjectTaskService.get_task_reviews(self.owner_user, task)[0]
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.volunteer_applicant_user],
                lambda x: ProjectTaskService.reject_task_review(x, self.project.id, task.id, task_review))
            ProjectTaskService.reject_task_review(self.owner_user, self.project.id, task.id, task_review)
            self.assertEqual(ProjectTaskService.get_project_task_review(self.owner_user, self.project.id, task.id, task_review.id).review_result, ReviewStatus.REJECTED)
            self.assertEqual(ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id).stage, TaskStatus.STARTED)

        with self.subTest(stage='Accept task review'):
            task_review = ProjectTaskReview()
            task_review.volunteer_comment = "Completed."
            task_review.volunteer_effort_hours = 1
            ProjectTaskService.mark_task_as_completed(self.volunteer_applicant_user, self.project.id, task.id, task_review)
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.volunteer_applicant_user],
                lambda x: ProjectTaskService.accept_task_review(x, self.project.id, task.id, task_review))
            self.assertEqual(len(self.volunteer_applicant_user.userbadge_set.all()), 1)
            task_review.review_score = Score.FIVE_STARS
            ProjectTaskService.accept_task_review(self.owner_user, self.project.id, task.id, task_review)
            self.assertEqual(ProjectTaskService.get_project_task_review(self.owner_user, self.project.id, task.id, task_review.id).review_result, ReviewStatus.ACCEPTED)
            self.assertEqual(ProjectTaskService.get_project_task(self.owner_user, self.project.id, task.id).stage, TaskStatus.COMPLETED)
            self.assertEqual(len(self.volunteer_applicant_user.userbadge_set.all()), 3)

        with self.subTest(stage='Pin task review'):
            task_reviews = ProjectTaskService.get_task_reviews(self.owner_user, task)
            for task_review in task_reviews:
                test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.owner_user, self.proj_mgmt_user, self.scoping_user, self.qa_user],
                    lambda x: ProjectTaskService.toggle_pinned_task_review(x, self.project.id, task.id, task_review.id))
                ProjectTaskService.toggle_pinned_task_review(self.volunteer_applicant_user, self.project.id, task.id, task_review.id)
            pinned_reviews = ProjectTaskService.get_pinned_task_reviews(AnonymousUser(), self.volunteer_applicant_user)
            self.assertEqual(len(pinned_reviews), len(task_reviews))

        with self.subTest(stage='Prevent deleting completed tasks'):
            with self.assertRaisesMessage(ValueError, ''):
                ProjectTaskService.delete_task(self.owner_user, self.project.id, task)

        with self.subTest(stage='Prevent marking as completed tasks that are already completed'):
            role = ProjectTaskService.get_own_project_task_role(self.volunteer_applicant_user, self.project.id, task.id)
            with self.assertRaisesMessage(ValueError, ''):
                ProjectTaskService.cancel_volunteering(self.volunteer_applicant_user, self.project.id, task.id, role)


        task2 = ProjectTaskService.create_default_task(self.scoping_user, self.project.id)
        task2.name = 'New edited task'
        task2.type = TaskType.DOMAIN_WORK_TASK
        ProjectTaskService.save_task(self.owner_user, self.project.id, task2.id, task2)
        ProjectTaskService.publish_project_task(self.owner_user, self.project.id, task2.id, task2)
        ProjectTaskService.toggle_task_accepting_volunteers(self.owner_user, self.project.id, task2.id)
        application = VolunteerApplication()
        application.volunteer_application_letter = "This is the letter."
        application.task = task2
        application.volunteer = self.volunteer_applicant_user
        ProjectTaskService.apply_to_volunteer(self.volunteer_applicant_user, self.project.id, task2.id, application)
        ProjectTaskService.accept_volunteer(self.scoping_user, self.project.id, task2.id, application)


        with self.subTest(stage='Task getters 2'):
            self.assertEqual(task2, ProjectTaskService.get_project_task(self.owner_user, self.project.id, task2.id))
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user],
                lambda x: ProjectTaskService.get_all_tasks(x, self.project))
            self.assertEqual(set(self.project.projecttask_set.all()), set(ProjectTaskService.get_all_tasks(self.owner_user, self.project)))

            self.assertEqual(set(ProjectTaskService.get_public_tasks(self.owner_user, self.project.id)),
                set([scoping_task, project_management_task, domain_work_task, qa_task, task, task2]))
            self.assertEqual(set(ProjectTaskService.get_project_tasks_summary(self.owner_user, self.project.id)),
                set([scoping_task, project_management_task, domain_work_task, qa_task, task, task2]))
            self.assertEqual(set(ProjectTaskService.get_non_finished_tasks(self.owner_user, self.project.id)),
                set([scoping_task, project_management_task, domain_work_task, qa_task, task2]))

            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.scoping_user, self.owner_user, self.qa_user],
                lambda x: ProjectTaskService.get_volunteer_current_tasks(x, self.volunteer_applicant_user, self.project.id))
            self.assertEqual(set(ProjectTaskService.get_volunteer_current_tasks(self.volunteer_applicant_user, self.volunteer_applicant_user, self.project.id)),
                set([task2]))
            self.assertEqual(set(ProjectTaskService.get_volunteer_all_project_tasks(self.volunteer_applicant_user, self.volunteer_applicant_user, self.project)),
                set([task, task2]))
            self.assertEqual(set(ProjectTaskService.get_volunteer_all_tasks(self.owner_user, self.volunteer_applicant_user)),
                set([task, task2]))
            self.assertEqual(set(ProjectTaskService.get_user_in_progress_tasks(self.volunteer_applicant_user)),
                set([task2]))

        with self.subTest(stage='Cancel volunteering'):
            role = ProjectTaskService.get_own_project_task_role(self.volunteer_applicant_user, self.project.id, task2.id)
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.scoping_user, self.owner_user, self.qa_user],
                lambda x: ProjectTaskService.cancel_volunteering(x, self.project.id, task2.id, role))
            ProjectTaskService.cancel_volunteering(self.volunteer_applicant_user, self.project.id, task2.id, role)
            self.assertFalse(ProjectTaskService.user_is_task_volunteer(self.volunteer_applicant_user, task2))
            with self.assertRaisesMessage(ProjectTaskRole.DoesNotExist, ''):
                ProjectTaskService.get_own_project_task_role(self.volunteer_applicant_user, self.project.id, task2.id)

        with self.subTest(stage='Delete task'):
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.qa_user],
                lambda x: ProjectTaskService.delete_task(x, self.project.id, task2))
            task2 = ProjectTaskService.create_default_task(self.scoping_user, self.project.id)
            ProjectTaskService.delete_task(self.owner_user, self.project.id, task2)
            task2 = ProjectTaskService.create_default_task(self.scoping_user, self.project.id)
            ProjectTaskService.delete_task(self.scoping_user, self.project.id, task2)

        with self.subTest(stage='Task staff'):
            self.assertEqual(set(ProjectTaskService.get_task_staff(self.owner_user, task.id)), set([]))
            self.assertEqual(ProjectTaskService.get_project_task_staff_for_editing(self.owner_user, self.project.id, task.id),
                [{'user': self.owner_user, 'assigned': None}, {'user': self.staff_user, 'assigned': None}])
            post_object = {str(self.owner_user.id): False, str(self.staff_user.id): True}
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.scoping_user, self.volunteer_applicant_user, self.qa_user],
                lambda x: ProjectTaskService.set_task_staff(x, self.project.id, task.id, post_object))
            ProjectTaskService.set_task_staff(self.owner_user, self.project.id, task.id, post_object)
            self.assertEqual(set(ProjectTaskService.get_task_staff(self.owner_user, task.id)), set([self.staff_user]))
            self.assertEqual(ProjectTaskService.get_project_task_staff_for_editing(self.owner_user, self.project.id, task.id),
                [{'user': self.owner_user, 'assigned': None}, {'user': self.staff_user, 'assigned': True}])


        with self.subTest(stage='Task roles'):
            staff_user_role = ProjectTaskRole.objects.get(user=self.staff_user, task=task)
            volunteer_user_role = ProjectTaskRole.objects.get(user=self.volunteer_applicant_user, task=task)

            self.assertEqual(staff_user_role, ProjectTaskService.get_project_task_role(self.owner_user, self.project.id, task.id, staff_user_role.id))
            self.assertEqual(volunteer_user_role, ProjectTaskService.get_project_task_role(self.owner_user, self.project.id, task.id, volunteer_user_role.id))
            self.assertEqual(staff_user_role, ProjectTaskService.get_own_project_task_role(self.staff_user, self.project.id, task.id))
            self.assertEqual(volunteer_user_role, ProjectTaskService.get_own_project_task_role(self.volunteer_applicant_user, self.project.id, task.id))

            volunteer_user_role.task = domain_work_task
            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.volunteer_applicant_user, self.qa_user],
                lambda x: ProjectTaskService.save_project_task_role(x, self.project.id, task.id, volunteer_user_role))
            ProjectTaskService.save_project_task_role(self.owner_user, self.project.id, task.id, volunteer_user_role)
            self.assertFalse(ProjectTaskService.user_is_task_volunteer(self.volunteer_applicant_user, task))
            self.assertTrue(ProjectTaskService.user_is_task_volunteer(self.volunteer_applicant_user, domain_work_task))
            self.assertTrue(ProjectTaskService.user_is_task_volunteer(self.volunteer_user, domain_work_task))
            self.assertEqual(len(ProjectTaskService.get_task_volunteers(self.owner_user, domain_work_task.id)), 2)

            test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.volunteer_applicant_user, self.qa_user],
                lambda x: ProjectTaskService.delete_project_task_role(x, self.project.id, task.id, volunteer_user_role))
            ProjectTaskService.delete_project_task_role(self.owner_user, self.project.id, domain_work_task.id, volunteer_user_role)
            self.assertFalse(ProjectTaskService.user_is_task_volunteer(self.volunteer_applicant_user, task))
            self.assertFalse(ProjectTaskService.user_is_task_volunteer(self.volunteer_applicant_user, domain_work_task))
            self.assertTrue(ProjectTaskService.user_is_task_volunteer(self.volunteer_user, domain_work_task))
            self.assertEqual(len(ProjectTaskService.get_task_volunteers(self.owner_user, domain_work_task.id)), 1)

        with self.subTest(stage='Task requirements'):
            skill1 = Skill()
            skill1.area = "Area 1"
            skill1.name = "Skill 1"
            skill1.save()
            skill2 = Skill()
            skill2.area = "Area 2"
            skill2.name = "Skill 2"
            skill2.save()
            self.assertEqual(ProjectTaskService.get_project_task_requirements(self.owner_user, self.project.id, task.id),
                {skill1.area: [{'system_skill': skill1, 'task_requirement': None}],
                 skill2.area: [{'system_skill': skill2, 'task_requirement': None}]})
            for level in [SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE, SkillLevel.EXPERT]:
                for importance in [TaskRequirementImportance.NICE_TO_HAVE, TaskRequirementImportance.IMPORTANT, TaskRequirementImportance.REQUIRED]:
                    with self.subTest(level=level, importance=importance):
                        post_object = {str(skill1.id): level, "i" + str(skill1.id): importance,
                                       str(skill2.id): -1}
                        test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.qa_user],
                            lambda x: ProjectTaskService.set_task_requirements(x, self.project.id, task.id, post_object))
                        ProjectTaskService.set_task_requirements(self.owner_user, self.project.id, task.id, post_object)
                        new_requirements = ProjectTaskService.get_project_task_requirements(self.owner_user, self.project.id, task.id)
                        saved_task_requirement = ProjectTaskRequirement.objects.get(task=task, skill=skill1)
                        self.assertEqual(saved_task_requirement.level, level)
                        self.assertEqual(saved_task_requirement.importance, importance)
                        self.assertEqual(new_requirements,
                            {skill1.area: [{'system_skill': skill1, 'task_requirement': saved_task_requirement}],
                             skill2.area: [{'system_skill': skill2, 'task_requirement': None}]})

    def test_project_status(self):
        scoping_task, project_management_task, domain_work_task, qa_task = self.create_standard_project_structure(False, False)
        project_changes = 8
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

        all_users = self.get_all_users()
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id).status, ProjectStatus.DRAFT)
        ProjectService.publish_project(self.owner_user, self.project.id, self.project)
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id).status, ProjectStatus.NEW)
        project_changes += 1
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

        scoping_application = scoping_task.volunteerapplication_set.first()
        ProjectTaskService.accept_volunteer(self.owner_user, self.project.id, scoping_task.id, scoping_application)
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id).status, ProjectStatus.DESIGN)
        project_changes += 2
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)
        task_review = ProjectTaskReview()
        task_review.volunteer_comment = "Completed."
        task_review.volunteer_effort_hours = 1
        ProjectTaskService.mark_task_as_completed(self.scoping_user, self.project.id, scoping_task.id, task_review)
        project_changes += 2
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)
        ProjectTaskService.accept_task_review(self.owner_user, self.project.id, scoping_task.id, task_review)
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id).status, ProjectStatus.WAITING_STAFF)
        project_changes += 2
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

        proj_mgm_application = project_management_task.volunteerapplication_set.first()
        ProjectTaskService.accept_volunteer(self.owner_user, self.project.id, project_management_task.id, proj_mgm_application)
        project_changes += 1
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

        qa_application = qa_task.volunteerapplication_set.first()
        ProjectTaskService.accept_volunteer(self.owner_user, self.project.id, qa_task.id, qa_application)
        project_changes += 1
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

        domain_work_application = domain_work_task.volunteerapplication_set.first()
        ProjectTaskService.accept_volunteer(self.owner_user, self.project.id, domain_work_task.id, domain_work_application)
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id).status, ProjectStatus.IN_PROGRESS)
        project_changes += 2
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

        task_review = ProjectTaskReview()
        task_review.volunteer_comment = "Completed."
        task_review.volunteer_effort_hours = 1
        ProjectTaskService.mark_task_as_completed(self.proj_mgmt_user, self.project.id, project_management_task.id, task_review)
        project_changes += 1
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)
        ProjectTaskService.accept_task_review(self.owner_user, self.project.id, project_management_task.id, task_review)
        project_changes += 1
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

        task_review = ProjectTaskReview()
        task_review.volunteer_comment = "Completed."
        task_review.volunteer_effort_hours = 1
        ProjectTaskService.mark_task_as_completed(self.qa_user, self.project.id, qa_task.id, task_review)
        project_changes += 1
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)
        ProjectTaskService.accept_task_review(self.owner_user, self.project.id, qa_task.id, task_review)
        project_changes += 1
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

        task_review = ProjectTaskReview()
        task_review.volunteer_comment = "Completed."
        task_review.volunteer_effort_hours = 1
        ProjectTaskService.mark_task_as_completed(self.volunteer_user, self.project.id, domain_work_task.id, task_review)
        project_changes += 1
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)
        ProjectTaskService.accept_task_review(self.owner_user, self.project.id, domain_work_task.id, task_review)
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id).status, ProjectStatus.WAITING_REVIEW)
        project_changes += 2
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

        test_permission_denied_operation(self, [AnonymousUser(), self.volunteer_user, self.staff_user, self.proj_mgmt_user, self.scoping_user, self.volunteer_applicant_user],
            lambda x: marketplace.project.finish_project(x, self.project))
        marketplace.project.finish_project(self.owner_user, ProjectService.get_project(self.owner_user, self.project.id))
        self.assertEqual(ProjectService.get_project(self.owner_user, self.project.id).status, ProjectStatus.COMPLETED)
        project_changes += 1
        self.assertEqual(len(ProjectService.get_project_changes(self.owner_user, self.project)), project_changes)

# TODO check that notifications are generated correctly on every action

# TODO check that all the paths within ProjectTaskService.save_task_internal are covered by tests
