from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .views import common, org, proj, user

app_name = 'dssgmkt'
urlpatterns = [
    path('', user.home_view, name='home'),
    path('about/', common.about_view, name='about'),


    path('org/', org.OrganizationIndexView.as_view(), name='org_list'),
    path('org/<int:org_pk>/', org.OrganizationView.as_view(), name='org_info'),
    path('org/<int:org_pk>/edit', org.OrganizationEdit.as_view(), name='org_info_edit'),
    path('org/<int:org_pk>/staff/', org.organization_staff_view, name='org_staff'),
    path('org/<int:org_pk>/staff/<int:role_pk>/edit', org.OrganizationRoleEdit.as_view(), name='org_staff_edit'),
    path('org/<int:org_pk>/staff/<int:role_pk>/remove', org.OrganizationRoleRemove.as_view(), name='org_staff_remove'),
    path('org/<int:org_pk>/staff/request', org.OrganizationMembershipRequestCreate.as_view(), name='org_staff_request'),
    path('org/<int:org_pk>/staff/leave', org.OrganizationLeave.as_view(), name='org_staff_leave'),
    path('org/<int:org_pk>/staff/request/<int:request_pk>/', org.process_organization_membership_request_view, name='org_staff_request_review'),
    path('org/<int:org_pk>/staff/request/<int:request_pk>/review/<str:action>', org.process_organization_membership_request_view, name='org_staff_request_review_do'),

    path('proj/', proj.ProjectIndexView.as_view(), name='proj_list'),
    path('proj/<int:proj_pk>/', proj.ProjectView.as_view(), name='proj_info'),
    path('proj/<int:proj_pk>/edit', proj.ProjectEdit.as_view(), name='proj_info_edit'),
    path('proj/<int:proj_pk>/publish', proj.publish_project_view, name='proj_publish'),
    path('proj/<int:proj_pk>/finish', proj.finish_project_view, name='proj_finish'),
    path('proj/<int:proj_pk>/follow', proj.follow_project_view, name='proj_follow'),
    path('proj/<int:proj_pk>/log/', proj.ProjectLogView.as_view(), name='proj_log'),
    path('proj/<int:proj_pk>/discussion/', proj.project_comments_view, name='proj_discussion'),
    path('proj/<int:proj_pk>/discussion/add', proj.project_comments_view, name='proj_discussion_add'),
    path('proj/<int:proj_pk>/deliverables/', proj.ProjectDeliverablesView.as_view(), name='proj_deliverables'),
    path('proj/<int:proj_pk>/instructions/', proj.ProjectVolunteerInstructionsView.as_view(), name='proj_instructions'),
    path('proj/<int:proj_pk>/task/', proj.ProjectTaskIndex.as_view(), name='proj_task_list'),
    path('proj/<int:proj_pk>/task/add', proj.create_default_project_task, name='proj_task_add'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/', proj.ProjectTaskDetailView.as_view(), name='proj_task'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/finish', proj.ProjectTaskReviewCreate.as_view(), name='proj_task_finish'),
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
    path('proj/<int:proj_pk>/task/<int:task_pk>/requirements/<int:requirement_pk>/edit', proj.ProjectTaskRequirementEdit.as_view(), name='proj_task_requirements_requirement_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/requirements/<int:requirement_pk>/remove', proj.ProjectTaskRequirementRemove.as_view(), name='proj_task_requirements_requirement_remove'),
    path('proj/<int:proj_pk>/staff', proj.project_staff_view, name='proj_staff'),
    path('proj/<int:proj_pk>/staff/<int:role_pk>/edit', proj.ProjectRoleEdit.as_view(), name='proj_staff_edit'),
    path('proj/<int:proj_pk>/staff/<int:role_pk>/remove', proj.ProjectRoleRemove.as_view(), name='proj_staff_remove'),
    path('proj/<int:proj_pk>/volunteers', proj.project_volunteers_view, name='proj_volunteers'),


    path('logout/', user.logout_view, name='logout'),
    path('login/', auth_views.LoginView.as_view(template_name='dssgmkt/login.html'), name='login'),
    path('user/pwdchange', auth_views.PasswordChangeView.as_view(template_name='dssgmkt/user_pwd_change.html',
                                                                 success_url=reverse_lazy('dssgmkt:my_user_profile'),
                                                                 extra_context={'breadcrumb':user.change_password_breadcrumb()}),name='user_pwd_change'),
    path('pwd/resetrequest', auth_views.PasswordResetView.as_view(template_name='dssgmkt/pwd_reset_request.html',
                                                                 success_url=reverse_lazy('dssgmkt:pwd_reset_request_done'),
                                                                 email_template_name='dssgmkt/password_reset_email.html',
                                                                 subject_template_name='dssgmkt/password_reset_email_subject.html'), name='pwd_reset_request'),
    path('pwd/resetrequest/done', auth_views.PasswordResetDoneView.as_view(template_name='dssgmkt/pwd_reset_request_done.html'), name='pwd_reset_request_done'),
    path('pwd/reset/<str:uidb64>/<str:token>', auth_views.PasswordResetConfirmView.as_view(template_name='dssgmkt/pwd_reset.html',
                                                                                            success_url=reverse_lazy('dssgmkt:pwd_reset_complete')), name='pwd_reset'),
    path('pwd/reset/done', auth_views.PasswordResetCompleteView.as_view(template_name='dssgmkt/pwd_reset_complete.html'), name='pwd_reset_complete'),


    path('volunteers/', user.VolunteerIndexView.as_view(), name='volunteer_list'),
    path('user/', user.my_user_profile_view, name='my_user_profile'),
    path('user/<int:user_pk>', user.UserProfileView.as_view(), name='user_profile'),
    path('user/<int:user_pk>/edit', user.UserProfileEdit.as_view(), name='user_profile_edit'),
    path('user/<int:user_pk>/volunteercreate', user.create_volunteer_profile_view, name='user_volunteer_profile_create'),
    path('user/<int:user_pk>/<int:volunteer_pk>/edit', user.VolunteerProfileEdit.as_view(), name='user_volunteer_profile_edit'),
    path('user/<int:user_pk>/skills', user.user_profile_skills_edit_view, name='user_profile_skills_edit'),
    path('user/<int:user_pk>/skills/<int:skill_pk>/edit', user.VolunteerSkillEdit.as_view(), name='user_profile_skills_skill_edit'),
    path('user/<int:user_pk>/skills/<int:skill_pk>/remove', user.VolunteerSkillRemove.as_view(), name='user_profile_skills_skill_remove'),

]
