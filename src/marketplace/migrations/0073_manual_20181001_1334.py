from django.db import migrations, models
import django.db.models.deletion
from dssgmkt.models.org import Organization, OrganizationSocialCause
from dssgmkt.models.proj import Project, ProjectSocialCause

def rebuild_organization_social_causes(apps, schema_editor):
    for org in Organization.objects.all():
        if org.main_cause and not OrganizationSocialCause.objects.filter(organization=org).exists():
            new_social_cause = OrganizationSocialCause()
            new_social_cause.social_cause = org.main_cause
            new_social_cause.organization = org
            new_social_cause.save()

def rebuild_project_social_causes(apps, schema_editor):
    for proj in Project.objects.all():
        if proj.project_cause and not ProjectSocialCause.objects.filter(project=proj).exists():
            new_social_cause = ProjectSocialCause()
            new_social_cause.social_cause = proj.project_cause
            new_social_cause.project = proj
            new_social_cause.save()

class Migration(migrations.Migration):

    dependencies = [
        ('dssgmkt', '0072_auto_20181001_1321'),
    ]

    operations = [
        migrations.RunPython(rebuild_organization_social_causes),
        migrations.RunPython(rebuild_project_social_causes),
    ]
