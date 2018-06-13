from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views

app_name = 'dssgmkt'
urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),


    path('org/', views.OrganizationIndexView.as_view(), name='org_list'),
    path('org/<int:pk>/', views.OrganizationView.as_view(), name='org_info'),
    path('org/<int:org_pk>/edit', views.OrganizationEdit.as_view(), name='org_info_edit'),
    path('org/<int:pk>/staff/', views.organization_staff_view, name='org_staff'),
    path('org/<int:org_pk>/staff/<int:role_pk>/edit', views.OrganizationRoleEdit.as_view(), name='org_staff_edit'),
    path('org/<int:org_pk>/staff/<int:role_pk>/remove', views.OrganizationRoleRemove.as_view(), name='org_staff_remove'),
    path('org/<int:org_pk>/staff/request', views.OrganizationMembershipRequestCreate.as_view(), name='org_staff_request'),
    path('org/<int:org_pk>/staff/leave', views.OrganizationLeave.as_view(), name='org_staff_leave'),
    path('org/<int:org_pk>/staff/request/<int:request_pk>/review', views.OrganizationMembershipRequestEdit.as_view(), name='org_staff_request_review'),


    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    # path('<int:question_id>/vote/', views.vote, name='vote'),
    path('proj/', views.ProjectIndexView.as_view(), name='proj_list'),
    path('proj/<int:proj_pk>/', views.ProjectView.as_view(), name='proj_info'),
    path('proj/<int:proj_pk>/edit', views.ProjectEdit.as_view(), name='proj_info_edit'),
    path('proj/<int:proj_pk>/follow', views.follow_project_view, name='proj_follow'),
    # path('proj/<int:pk>/log/', views.ProjectLogView.as_view(), name='proj_log'),
    path('proj/<int:proj_pk>/log/', views.ProjectLogView.as_view(), name='proj_log'),
    path('proj/<int:proj_pk>/deliverables/', views.ProjectDeliverablesView.as_view(), name='proj_deliverables'),
    path('proj/<int:proj_pk>/instructions/', views.ProjectVolunteerInstructionsView.as_view(), name='proj_instructions'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/finish', views.ProjectTaskReviewCreate.as_view(), name='proj_task_finish'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/cancel', views.ProjectTaskCancel.as_view(), name='proj_task_cancel'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/apply', views.ProjectTaskApply.as_view(), name='proj_task_apply'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/edit', views.ProjectTaskEdit.as_view(), name='proj_task_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/delete', views.ProjectTaskRemove.as_view(), name='proj_task_remove'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/volunteer/<int:task_role_pk>', views.ProjectTaskRoleRemove.as_view(), name='proj_volunteer_remove'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/volunteer/application/<int:volunteer_application_pk>/review', views.ProjectVolunteerApplicationEdit.as_view(), name='proj_volunteer_application_review'),
    path('proj/<int:proj_pk>/task/', views.ProjectTaskIndex.as_view(), name='proj_task_list'),
    path('proj/<int:proj_pk>/task/add', views.create_default_project_task, name='proj_task_add'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/requirements', views.project_task_requirements_edit_view, name='proj_task_requirements_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/requirements/<int:requirement_pk>/edit', views.ProjectTaskRequirementEdit.as_view(), name='proj_task_requirements_requirement_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/requirements/<int:requirement_pk>/remove', views.ProjectTaskRequirementRemove.as_view(), name='proj_task_requirements_requirement_remove'),
    path('proj/<int:proj_pk>/staff', views.project_staff_view, name='proj_staff'),
    path('proj/<int:proj_pk>/staff/<int:role_pk>/edit', views.ProjectRoleEdit.as_view(), name='proj_staff_edit'),
    path('proj/<int:proj_pk>/staff/<int:role_pk>/remove', views.ProjectRoleRemove.as_view(), name='proj_staff_remove'),

    path('logout/', views.logout_view, name='logout'),
    path('login/', auth_views.LoginView.as_view(template_name='dssgmkt/login.html'), name='login'),
    path('user/pwdchange', auth_views.PasswordChangeView.as_view(template_name='dssgmkt/user_pwd_change.html',
                                                                 success_url=reverse_lazy('dssgmkt:my_user_profile')), name='user_pwd_change'),
    path('pwd/resetrequest', auth_views.PasswordResetView.as_view(template_name='dssgmkt/pwd_reset_request.html',
                                                                 success_url=reverse_lazy('dssgmkt:pwd_reset_request_done'),
                                                                 email_template_name='dssgmkt/password_reset_email.html',
                                                                 subject_template_name='dssgmkt/password_reset_email_subject.html'), name='pwd_reset_request'),
    path('pwd/resetrequest/done', auth_views.PasswordResetDoneView.as_view(template_name='dssgmkt/pwd_reset_request_done.html'), name='pwd_reset_request_done'),
    path('pwd/reset/<str:uidb64>/<str:token>', auth_views.PasswordResetConfirmView.as_view(template_name='dssgmkt/pwd_reset.html',
                                                                                            success_url=reverse_lazy('dssgmkt:pwd_reset_complete')), name='pwd_reset'),
    path('pwd/reset/done', auth_views.PasswordResetCompleteView.as_view(template_name='dssgmkt/pwd_reset_complete.html'), name='pwd_reset_complete'),


    path('user/', views.my_user_profile_view, name='my_user_profile'),
    path('user/<int:user_pk>', views.UserProfileView.as_view(), name='user_profile'),
    path('user/<int:user_pk>/edit', views.UserProfileEdit.as_view(), name='user_profile_edit'),
    path('user/<int:user_pk>/<int:volunteer_pk>/edit', views.VolunteerProfileEdit.as_view(), name='user_volunteer_profile_edit'),

    path('user/<int:user_pk>/skills', views.user_profile_skills_edit_view, name='user_profile_skills_edit'),
    path('user/<int:user_pk>/skills/<int:skill_pk>/edit', views.VolunteerSkillEdit.as_view(), name='user_profile_skills_skill_edit'),
    path('user/<int:user_pk>/skills/<int:skill_pk>/remove', views.VolunteerSkillRemove.as_view(), name='user_profile_skills_skill_remove'),

]
