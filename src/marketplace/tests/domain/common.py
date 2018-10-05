from django.utils import timezone
from django.core.exceptions import PermissionDenied

from marketplace.models.common import ReviewStatus, SocialCause
from marketplace.models.user import User
from marketplace.models.proj import Project
from marketplace.models.org import Organization, Budget, YearsInOperation, GeographicalScope


def example_organization_user():
    organization_user = User()
    organization_user.username = "OrgUser"
    organization_user.first_name = "Organization"
    organization_user.last_name = "User"
    return organization_user

def example_staff_user():
    staff_user = User()
    staff_user.username = "StaffUser"
    staff_user.first_name = "Staff"
    staff_user.last_name = "User"
    return staff_user

def example_volunteer_user(username="VolUser"):
    volunteer_user = User()
    volunteer_user.username = username
    volunteer_user.first_name = "Volunteer"
    volunteer_user.last_name = "User"
    volunteer_user.email = "volunteer@email.com"
    return volunteer_user

def example_organization():
    organization = Organization()
    organization.name = "Organization A"
    organization.short_summary = "A short description of the org"
    organization.description = "A long form description of the organization"
    organization.website_url = "http://exampleorg.com"
    organization.phone_number = "(111)111-1111"
    organization.email_address = "email@org.org"
    organization.street_address = "1 One Street"
    organization.city = "OrgCity"
    organization.state = "OrgState"
    organization.zipcode = "11111"
    organization.budget = Budget.B100K
    organization.years_operation = YearsInOperation.Y0
    organization.organization_scope = GeographicalScope.LOCAL
    return organization

def example_project():
    project = Project()
    project.name = 'Demo project 1'
    project.short_summary = 'A very short summary of the project'

    project.motivation = 'The project motivation'
    project.solution_description = 'The project description'
    project.project_impact = 'The project impact'
    project.stakeholders = 'The project stakeholders'
    project.available_staff = 'The available staff'

    project.banner_image_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/1_Pangong_lake.jpg/320px-1_Pangong_lake.jpg'
    project.project_cause = SocialCause.ENERGY

    project.scope_goals = 'The project goals'
    project.scope_interventions = 'The project interventions'
    project.scope_available_data = 'The available data'
    project.scope_analysis = 'The project analysis'
    project.scope_validation_methodology = 'The validation methodology'
    project.scope_implementation = 'The implementation plan'

    project.developer_agreement = 'By clicking accept you agree that the data and work will belong to the organization.'
    project.intended_start_date = timezone.now()
    project.intended_end_date = timezone.now()
    project.deliverables_description = 'This is the description of the deliverables of the project'
    project.deliverable_github_url = None
    project.deliverable_management_url = None
    project.deliverable_documentation_url = None
    project.deliverable_reports_url = None
    project.is_demo = False
    return project


def test_users_group_inclusion(test_case, all_users, included_users, predicate):
    for user in all_users:
        with test_case.subTest(user=user):
            test_case.assertEqual(predicate(user), user in included_users)

def test_permission_denied_operation(test_case, users, operation):
    for user in users:
        with test_case.subTest(user=user):
            with test_case.assertRaisesMessage(PermissionDenied, ''):
                operation(user)
