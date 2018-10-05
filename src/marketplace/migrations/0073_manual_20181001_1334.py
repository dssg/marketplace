from django.db import migrations


def rebuild_organization_social_causes(apps, schema_editor):
    Organization = apps.get_model('marketplace', 'Organization')
    OrganizationSocialCause = apps.get_model('marketplace', 'OrganizationSocialCause')

    organizations = (Organization.objects
                     .exclude(main_cause='')
                     .filter(organizationsocialcause=None))

    OrganizationSocialCause.objects.bulk_create([
        OrganizationSocialCause(
            social_cause=organization.main_cause,
            organization=organization,
        )
        for organization in organizations.iterator()
    ])


def rebuild_project_social_causes(apps, schema_editor):
    Project = apps.get_model('marketplace', 'Project')
    ProjectSocialCause = apps.get_model('marketplace', 'ProjectSocialCause')

    projects = (Project.objects
                .exclude(project_cause='')
                .filter(projectsocialcause=None))

    ProjectSocialCause.objects.bulk_create([
        ProjectSocialCause(
            social_cause=project.project_cause,
            project=project,
        )
        for project in projects.iterator()
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0072_auto_20181001_1321'),
    ]

    operations = [
        migrations.RunPython(rebuild_organization_social_causes),
        migrations.RunPython(rebuild_project_social_causes),
    ]
