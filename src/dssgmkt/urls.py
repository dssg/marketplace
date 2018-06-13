from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from .views import commonviews, orgviews, projviews, userviews

app_name = 'dssgmkt'
urlpatterns = [
    path('', commonviews.home_view, name='home'),
    path('about/', commonviews.about_view, name='about'),


    path('org/', orgviews.OrganizationIndexView.as_view(), name='org_list'),
    path('org/<int:pk>/', orgviews.OrganizationView.as_view(), name='org_info'),
    path('org/<int:org_pk>/edit', orgviews.OrganizationEdit.as_view(), name='org_info_edit'),
    path('org/<int:pk>/staff/', orgviews.organization_staff_view, name='org_staff'),
    path('org/<int:org_pk>/staff/<int:role_pk>/edit', orgviews.OrganizationRoleEdit.as_view(), name='org_staff_edit'),
    path('org/<int:org_pk>/staff/<int:role_pk>/remove', orgviews.OrganizationRoleRemove.as_view(), name='org_staff_remove'),
    path('org/<int:org_pk>/staff/request', orgviews.OrganizationMembershipRequestCreate.as_view(), name='org_staff_request'),
    path('org/<int:org_pk>/staff/leave', orgviews.OrganizationLeave.as_view(), name='org_staff_leave'),
    path('org/<int:org_pk>/staff/request/<int:request_pk>/review', orgviews.OrganizationMembershipRequestEdit.as_view(), name='org_staff_request_review'),


    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    # path('<int:question_id>/vote/', views.vote, name='vote'),
    path('proj/', projviews.ProjectIndexView.as_view(), name='proj_list'),
    path('proj/<int:proj_pk>/', projviews.ProjectView.as_view(), name='proj_info'),
    path('proj/<int:proj_pk>/edit', projviews.ProjectEdit.as_view(), name='proj_info_edit'),
    path('proj/<int:proj_pk>/follow', projviews.follow_project_view, name='proj_follow'),
    # path('proj/<int:pk>/log/', views.ProjectLogView.as_view(), name='proj_log'),
    path('proj/<int:proj_pk>/log/', projviews.ProjectLogView.as_view(), name='proj_log'),
    path('proj/<int:proj_pk>/deliverables/', projviews.ProjectDeliverablesView.as_view(), name='proj_deliverables'),
    path('proj/<int:proj_pk>/instructions/', projviews.ProjectVolunteerInstructionsView.as_view(), name='proj_instructions'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/finish', projviews.ProjectTaskReviewCreate.as_view(), name='proj_task_finish'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/cancel', projviews.ProjectTaskCancel.as_view(), name='proj_task_cancel'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/apply', projviews.ProjectTaskApply.as_view(), name='proj_task_apply'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/edit', projviews.ProjectTaskEdit.as_view(), name='proj_task_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/delete', projviews.ProjectTaskRemove.as_view(), name='proj_task_remove'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/volunteer/<int:task_role_pk>', projviews.ProjectTaskRoleRemove.as_view(), name='proj_volunteer_remove'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/volunteer/application/<int:volunteer_application_pk>/review', projviews.ProjectVolunteerApplicationEdit.as_view(), name='proj_volunteer_application_review'),
    path('proj/<int:proj_pk>/task/', projviews.ProjectTaskIndex.as_view(), name='proj_task_list'),
    path('proj/<int:proj_pk>/task/add', projviews.create_default_project_task, name='proj_task_add'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/requirements', projviews.project_task_requirements_edit_view, name='proj_task_requirements_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/requirements/<int:requirement_pk>/edit', projviews.ProjectTaskRequirementEdit.as_view(), name='proj_task_requirements_requirement_edit'),
    path('proj/<int:proj_pk>/task/<int:task_pk>/requirements/<int:requirement_pk>/remove', projviews.ProjectTaskRequirementRemove.as_view(), name='proj_task_requirements_requirement_remove'),
    path('proj/<int:proj_pk>/staff', projviews.project_staff_view, name='proj_staff'),
    path('proj/<int:proj_pk>/staff/<int:role_pk>/edit', projviews.ProjectRoleEdit.as_view(), name='proj_staff_edit'),
    path('proj/<int:proj_pk>/staff/<int:role_pk>/remove', projviews.ProjectRoleRemove.as_view(), name='proj_staff_remove'),

    path('logout/', userviews.logout_view, name='logout'),
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


    path('user/', userviews.my_user_profile_view, name='my_user_profile'),
    path('user/<int:user_pk>', userviews.UserProfileView.as_view(), name='user_profile'),
    path('user/<int:user_pk>/edit', userviews.UserProfileEdit.as_view(), name='user_profile_edit'),
    path('user/<int:user_pk>/<int:volunteer_pk>/edit', userviews.VolunteerProfileEdit.as_view(), name='user_volunteer_profile_edit'),
    path('user/<int:user_pk>/skills', userviews.user_profile_skills_edit_view, name='user_profile_skills_edit'),
    path('user/<int:user_pk>/skills/<int:skill_pk>/edit', userviews.VolunteerSkillEdit.as_view(), name='user_profile_skills_skill_edit'),
    path('user/<int:user_pk>/skills/<int:skill_pk>/remove', userviews.VolunteerSkillRemove.as_view(), name='user_profile_skills_skill_remove'),

]
