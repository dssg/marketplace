from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from argparse import RawTextHelpFormatter
from csv import DictReader
import os

from dssgmkt.domain.org import OrganizationService
from dssgmkt.domain.proj import ProjectService
from dssgmkt.domain.user import UserService
from dssgmkt.models.proj import Project

class Command(BaseCommand):
    help = '''Loads a list of projects from a csv file.\n

The fields org_pk and user_pk represent the IDs of the organization that will
own the project and the user that will be assigned as first administrator of
the project. These IDs must exist before loading the projects, and the user
assigned as project owner must belong to the organization  that the project is
created under.

The banner image must be specified through a URL, so it has to be hosted elsewhere.

The 'status' field is *HIGHLY RECOMMENDED* to be set to value NW . Possible values are:
        Field value	Project status
        --------------------------------
        DR    		Draft
        NW    		New
        DE    		Scoping
        DA    		Scoping QA
        WS    		Waiting for volunteers
        IP    		In progress
        WR    		Final QA
        CO    		Completed
        EX    		Expired
        RM    		Deleted (currently not in use)

The 'project_cause' field must be set to one of:
        Field value	Social cause
        --------------------------------
        ED    		Education
        HE    		Health
        EN    		Environment
        SS    		Social_services
        TR    		Transportation
        EE    		Energy
        ID    		International development
        PS    		Public Safety
        EC    		Economic Development
        OT    		Other'''

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.formatter_class = RawTextHelpFormatter
        parser.add_argument(
            '--file', dest='file_path', default=os.path.join(settings.BASE_DIR,'dssgmkt','data','sample_projects.csv'),
            help='Specifies the CSV file to load project data from. If not provided, the command will load sample projects fom dssgmkt/data/sample_projects.csv',
        )

    def handle(self, *args, **options):
        path = options.get('file_path')
        self.stdout.write('Loading projects file {0}'.format(path))
        with open(path) as csvfile:
            reader = DictReader(csvfile)
            # ['user_pk', 'org_pk',
            #     'name', 'short_summary', 'motivation','solution_description',
            #     'challenges', 'banner_image_url', 'project_cause', 'project_impact',
            #     'scoping_process', 'available_staff', 'available_data',
            #     'developer_agreement', 'intended_start_date',
            #     'intended_end_date', 'status', 'deliverables_description',
            #     'deliverable_github_url', 'deliverable_management_url',
            #     'deliverable_documentation_url', 'deliverable_reports_url',
            #     'is_demo'])
            for row in reader:
                new_project = Project()
                new_project.name = row['name']
                new_project.short_summary = row['short_summary']
                new_project.motivation = row['motivation']
                new_project.solution_description = row['solution_description']
                new_project.challenges = row['challenges']
                new_project.banner_image_url = row['banner_image_url']
                new_project.project_cause = row['project_cause']
                new_project.project_impact = row['project_impact']
                new_project.scoping_process = row['scoping_process']
                new_project.available_staff = row['available_staff']
                new_project.available_data = row['available_data']
                new_project.developer_agreement = row['developer_agreement']
                new_project.intended_start_date = row['intended_start_date']
                new_project.intended_end_date =  row['intended_end_date']
                new_project.status = row['status']
                new_project.deliverables_description = row['deliverables_description']
                new_project.deliverable_github_url = row['deliverable_github_url']
                new_project.deliverable_management_url = row['deliverable_management_url']
                new_project.deliverable_documentation_url = row['deliverable_documentation_url']
                new_project.deliverable_reports_url = row['deliverable_reports_url']
                new_project.is_demo = row['is_demo']
                try:
                    organization_pk = int(row['org_pk'])
                    user_pk = int(row['user_pk'])
                    owner = UserService.get_user(None, user_pk)
                    OrganizationService.create_project(owner, organization_pk, new_project)
                    if row['status']:
                        new_project.status = row['status']
                        ProjectService.save_project(owner, new_project.id, new_project)
                    self.stdout.write('Created project {0}'.format(new_project))
                except Exception as e:
                    print(str(e))
                    self.stdout.write(self.style.WARNING('Failed to create project {0}'.format(new_project)))
        self.stdout.write(self.style.SUCCESS('Finished loading projects.'))
