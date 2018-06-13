from django.contrib import admin
from .models import Skill, Organization, Project, ProjectLog, ProjectFollower, ProjectTask, \
ProjectTaskReview, ProjectTaskRequirement, VolunteerApplication, User, VolunteerProfile, \
VolunteerSkill, OrganizationMembershipRequest, OrganizationRole, ProjectRole, ProjectTaskRole

admin.site.register(Skill)
admin.site.register(Organization)
admin.site.register(Project)
admin.site.register(ProjectLog)
admin.site.register(ProjectFollower)
admin.site.register(ProjectTask)
admin.site.register(ProjectTaskReview)
admin.site.register(ProjectTaskRequirement)
admin.site.register(VolunteerApplication)
admin.site.register(User)
admin.site.register(VolunteerProfile)
admin.site.register(VolunteerSkill)
admin.site.register(OrganizationMembershipRequest)
admin.site.register(OrganizationRole)
admin.site.register(ProjectRole)
admin.site.register(ProjectTaskRole)
