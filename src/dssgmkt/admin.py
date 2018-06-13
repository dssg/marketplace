from django.contrib import admin
# from .models import Skill, Organization, Project, ProjectLog, ProjectFollower, ProjectTask, \
# ProjectTaskReview, ProjectTaskRequirement, VolunteerApplication, User, VolunteerProfile, \
# VolunteerSkill, OrganizationMembershipRequest, OrganizationRole, ProjectRole, ProjectTaskRole


from .models import orgmodels, projmodels, usermodels

admin.site.register(usermodels.Skill)
admin.site.register(orgmodels.Organization)
admin.site.register(projmodels.Project)
admin.site.register(projmodels.ProjectLog)
admin.site.register(projmodels.ProjectFollower)
admin.site.register(projmodels.ProjectTask)
admin.site.register(projmodels.ProjectTaskReview)
admin.site.register(projmodels.ProjectTaskRequirement)
admin.site.register(projmodels.VolunteerApplication)
admin.site.register(usermodels.User)
admin.site.register(usermodels.VolunteerProfile)
admin.site.register(usermodels.VolunteerSkill)
admin.site.register(orgmodels.OrganizationMembershipRequest)
admin.site.register(orgmodels.OrganizationRole)
admin.site.register(projmodels.ProjectRole)
admin.site.register(projmodels.ProjectTaskRole)
