from django.contrib import admin

from .models import org, proj, user, news


class ProjectAdmin(admin.ModelAdmin):

    list_display = ('name', 'organization', 'status', 'creation_date')
    list_filter = ('status',)
    search_fields = ('name', 'organization__name')

    ordering = ('-creation_date',)


class UserAdmin(admin.ModelAdmin):

    fields = (
        'username',
        'email',
        'initial_type',
        'first_name',
        'last_name',
        'skype_name',
        'phone_number',
        'profile_image_file',
        'is_active',
        'is_staff',
        'is_superuser',
        'groups',
        'user_permissions',
        'date_joined',
        'last_login',
    )
    readonly_fields = ('date_joined', 'last_login')

    list_display = search_fields = ('username', 'email', 'first_name', 'last_name')

    ordering = ('-date_joined',)


admin.site.register(user.Skill)
admin.site.register(org.Organization)
admin.site.register(proj.Project, ProjectAdmin)
admin.site.register(proj.ProjectScope)
admin.site.register(proj.ProjectLog)
admin.site.register(proj.ProjectDiscussionChannel)
admin.site.register(proj.ProjectComment)
admin.site.register(proj.ProjectFollower)
admin.site.register(proj.ProjectTask)
admin.site.register(proj.ProjectTaskReview)
admin.site.register(proj.PinnedTaskReview)
admin.site.register(proj.ProjectTaskRequirement)
admin.site.register(proj.VolunteerApplication)
admin.site.register(user.User, UserAdmin)
admin.site.register(user.UserNotification)
admin.site.register(user.VolunteerProfile)
admin.site.register(user.VolunteerSkill)
admin.site.register(user.UserBadge)
admin.site.register(user.SignupCode)
admin.site.register(user.UserTaskPreference)
admin.site.register(org.OrganizationMembershipRequest)
admin.site.register(org.OrganizationRole)
admin.site.register(proj.ProjectRole)
admin.site.register(proj.ProjectTaskRole)
admin.site.register(news.NewsPiece)
