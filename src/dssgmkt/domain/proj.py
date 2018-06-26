

from django.db.models import Case, Q, When
from ..models.proj import (
    Project, ProjectStatus
)


class ProjectService():
    @staticmethod
    def get_all_organization_projects(request_user, org):
        return Project.objects.filter(organization=org)

    @staticmethod
    def get_organization_public_projects(request_user, org):
        return ProjectService.get_all_organization_projects(request_user, org) \
                                .exclude(status=ProjectStatus.DRAFT) \
                                .exclude(status=ProjectStatus.EXPIRED) \
                                .exclude(status=ProjectStatus.DELETED)
