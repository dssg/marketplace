from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView, TemplateView

from .views import common, org, proj, user, admin


# Set URL namespace
app_name = 'marketplace'

urlpatterns = [
    path('', user.home_view, name='home'),

    path('about/', common.about_view, name='about'),
    path('resources/', common.resources_view, name='resources'),

    path('terms/', RedirectView.as_view(pattern_name='marketplace:terms-20200804'), name='terms'),
    path('terms-20200804.html',
         TemplateView.as_view(template_name='marketplace/terms/terms-20200804.html',
                              extra_context={'privacy_url': 'marketplace:privacy-20200804'}),
         name='terms-20200804'),

    path('privacy/', RedirectView.as_view(pattern_name='marketplace:privacy-20200804'), name='privacy'),
    path('privacy-20200804.html',
         TemplateView.as_view(template_name='marketplace/privacy/privacy-20200804.html',
                              extra_context={'terms_url': 'marketplace:terms-20200804'}),
         name='privacy-20200804'),

    path('org/', org.organization_list_view, name='org_list'),
    path('org/create', org.OrganizationCreateView.as_view(), name='org_create'),
    path('org/create/<str:type>', org.OrganizationCreateView.as_view(), name='org_create_type'),
    path('org/<int:org_pk>/', org.OrganizationView.as_view(), name='org_info'),
    path('org/<int:org_pk>/edit', org.OrganizationEdit.as_view(), name='org_info_edit'),
    path('org/<int:org_pk>/staff/', org.organization_staff_view, name='org_staff'),
    path('org/<int:org_pk>/staff/add', org.add_organization_staff_view, name='org_staff_add'),
    path('org/<int:org_pk>/staff/<int:role_pk>/edit', org.OrganizationRoleEdit.as_view(), name='org_staff_edit'),
    path('org/<int:org_pk>/staff/<int:role_pk>/remove', org.organization_role_delete_view, name='org_staff_remove'),
    path('org/<int:org_pk>/staff/request', org.OrganizationMembershipRequestCreate.as_view(), name='org_staff_request'),
    path('org/<int:org_pk>/staff/leave', org.OrganizationLeave.as_view(), name='org_staff_leave'),
    path('org/<int:org_pk>/staff/request/<int:request_pk>/', org.process_organization_membership_request_view, name='org_staff_request_review'),
    path('org/<int:org_pk>/staff/request/<int:request_pk>/review/<str:action>', org.process_organization_membership_request_view, name='org_staff_request_review_do'),
    path('org/<int:org_pk>/createproject', proj.ProjectCreateView.as_view(), name='proj_create'),
    path('org/createproject/select', proj.project_create_select_organization_view, name='proj_create_org_select'),

    path('proj/', proj.project_list_view, name='proj_list'),
    path('proj/<int:proj_pk>/', proj.ProjectView.as_view(), name='proj_info'),
    path('proj/<int:proj_pk>/edit', proj.ProjectEdit.as_view(), name='proj_info_edit'),
    path('proj/<int:proj_pk>/publish', proj.publish_project_view, name='proj_publish'),
    path('proj/<int:proj_pk>/finish', proj.finish_project_view, name='proj_finish'),
    path('proj/<int:proj_pk>/follow', proj.follow_project_view, name='proj_follow'),
    path('proj/<int:proj_pk>/log/', proj.ProjectLogView.as_view(), name='proj_log'),
    path('proj/<int:proj_pk>/discussion/', proj.project_comment_channel_index_view, name='proj_discussion'),
    path('proj/<int:proj_pk>/discussion/<int:channel_pk>/', proj.project_channel_comments_view, name='proj_discussion'),
    path('proj/<int:proj_pk>/discussion/<int:channel_pk>/add', proj.project_channel_comments_view, name='proj_discussion_add'),
    path('proj/<int:proj_pk>/scope/', proj.project_scope_view, name='proj_scope'),
    path('proj/<int:proj_pk>/scope/<int:scope_pk>/', proj.project_scope_view, name='proj_scope_previous'),
    path('proj/<int:proj_pk>/scope/<int:scope_pk>/edit', proj.project_edit_scope_view, name='proj_scope_edit'),
    path('proj/<int:proj_pk>/deliverables/', proj.ProjectDeliverablesView.as_view(), name='proj_deliverables'),
    path('proj/<int:proj_pk>/instructions/', proj.ProjectVolunteerInstructionsView.as_view(), name='proj_instructions'),
    path('proj/<int:proj_pk>/instructions/<int:task_pk>/', proj.ProjectVolunteerTaskDetailView.as_view(), name='proj_instructions_task'),
    path('proj/<int:proj_pk>/instructions/<int:task_pk>/review/<int:review_pk>/pin', proj.pin_task_review_view, name='proj_instructions_task_review_pin'),
    path('proj/<int:proj_pk>/task/', proj.ProjectTaskIndex.as_view(), name='proj_task_list'),
    path('proj/<int:proj_pk>/task/add', proj.create_default_project_task, name='proj_task_add'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/', proj.ProjectTaskDetailView.as_view(), name='proj_task'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/finish', proj.ProjectTaskReviewCreate.as_view(), name='proj_task_finish'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/publish', proj.publish_project_task_view, name='proj_task_publish'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/review/<int:review_pk>/', proj.process_task_review_request_view, name='proj_task_review'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/review/<int:review_pk>/resolve/<str:action>', proj.process_task_review_request_view, name='proj_task_review_do'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/cancel', proj.ProjectTaskCancel.as_view(), name='proj_task_cancel'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/apply', proj.ProjectTaskApply.as_view(), name='proj_task_apply'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/edit', proj.ProjectTaskEdit.as_view(), name='proj_task_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/togglevolunteers', proj.toggle_task_accepting_volunteers_view, name='proj_task_toggle_volunteers'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/delete', proj.ProjectTaskRemove.as_view(), name='proj_task_remove'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/volunteer/<int:task_role_pk>', proj.ProjectTaskRoleRemove.as_view(), name='proj_volunteer_remove'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/volunteer/<int:task_role_pk>/edit', proj.ProjectTaskRoleEdit.as_view(), name='proj_volunteer_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/volunteer/application/<int:volunteer_application_pk>/', proj.volunteer_application_view, name='proj_volunteer_application_review'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/volunteer/application/<int:volunteer_application_pk>/<str:action>', proj.volunteer_application_view, name='proj_volunteer_application_review_do'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/requirements', proj.project_task_requirements_edit_view, name='proj_task_requirements_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/staff', proj.project_task_staff_edit_view, name='proj_task_staff_edit'),
    path('proj/<int:proj_pk>/staff', proj.project_staff_view, name='proj_staff'),
    path('proj/<int:proj_pk>/staff/<int:role_pk>/edit', proj.ProjectRoleEdit.as_view(), name='proj_staff_edit'),
    path('proj/<int:proj_pk>/staff/<int:role_pk>/remove', proj.project_role_delete_view, name='proj_staff_remove'),
    path('proj/<int:proj_pk>/volunteers', proj.project_volunteers_view, name='proj_volunteers'),

    path('logout/', user.logout_view, name='logout'),
    path('login/', user.login_view, name='login'),

    path('signup/select', user.select_user_type_before, name='signup_type_select'),
    path('signup/do/<str:user_type>', user.signup, name='signup_form'),
    path('signup/do/<str:user_type>/via/<str:provider_id>/', user.signup_oauth, name='signup_oauth'),

    path('user/pwdchange', user.change_password, name='user_pwd_change'),
    path('user/pwdset', user.set_password, name='user_pwd_set'),
    path('user/connections/', user.social_connections, name='user_social_connections'),

    path('pwd/resetrequest', auth_views.PasswordResetView.as_view(template_name='marketplace/pwd_reset_request.html',
                                                                 success_url=reverse_lazy('marketplace:pwd_reset_request_done'),
                                                                 email_template_name='marketplace/password_reset_email.html',
                                                                 subject_template_name='marketplace/password_reset_email_subject.html'), name='pwd_reset_request'),
    path('pwd/resetrequest/done', auth_views.PasswordResetDoneView.as_view(template_name='marketplace/pwd_reset_request_done.html'), name='pwd_reset_request_done'),
    path('pwd/reset/<str:uidb64>/<str:token>', auth_views.PasswordResetConfirmView.as_view(template_name='marketplace/pwd_reset.html',
                                                                                            success_url=reverse_lazy('marketplace:pwd_reset_complete')), name='pwd_reset'),
    path('pwd/reset/done', auth_views.PasswordResetCompleteView.as_view(template_name='marketplace/pwd_reset_complete.html'), name='pwd_reset_complete'),

    path('volunteers/', user.volunteer_list_view, name='volunteer_list'),
    path('user/', user.my_user_profile_view, name='my_user_profile'),
    path('user/dashboard/', user.UserHomeView.as_view(), name='user_dashboard'),
    path('user/select/', user.select_user_type_after, name='user_type_select'),
    path('user/<int:user_pk>', user.UserProfileView.as_view(), name='user_profile'),
    path('user/<int:user_pk>/edit', user.UserProfileEdit.as_view(), name='user_profile_edit'),
    path('user/<int:user_pk>/volunteercreate', user.create_volunteer_profile_view, name='user_volunteer_profile_create'),
    path('user/<int:user_pk>/<int:volunteer_pk>/edit', user.VolunteerProfileEdit.as_view(), name='user_volunteer_profile_edit'),
    path('user/<int:user_pk>/skills', user.user_profile_skills_edit_view, name='user_profile_skills_edit'),
    path('user/<int:user_pk>/preferences', user.user_preferences_edit_view, name='user_preferences_edit'),

    path('dssgadmin/', admin.AdminHomeView.as_view(), name='admin_home'),
    path('dssgadmin/<int:volunteer_pk>/review/<str:action>', admin.review_volunteer_profile_view, name='admin_volunteer_review'),

    path('ajax/org/<int:org_pk>/candidates/', org.get_all_users_not_organization_members_json, name='validate_username'),
    path('ajax/org/<int:org_pk>/candidates/<str:query>', org.get_all_users_not_organization_members_json, name='validate_username_do'),
]
