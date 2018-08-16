from datetime import date

from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Q
from django.forms import ModelForm
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.conf import settings
from rules.contrib.views import (
    PermissionRequiredMixin, objectgetter, permission_required,
)

from ..models.org import Organization, OrganizationMembershipRequest
from ..models.proj import Project, ProjectStatus, ProjectTask, VolunteerApplication
from ..models.user import Skill, SkillLevel, User, VolunteerProfile, VolunteerSkill, UserNotification, NotificationSource
from .common import build_breadcrumb, home_link, paginate

from dssgmkt.domain.user import UserService
from dssgmkt.domain.proj import ProjectService, ProjectTaskService
from dssgmkt.domain.org import OrganizationService
from dssgmkt.domain.notifications import NotificationService
from dssgmkt.domain.news import NewsService


def users_link(include_link=True):
    return ('Users', reverse_lazy('dssgmkt:volunteer_list') if include_link else None)

def volunteers_link(include_link=True):
    return ('Volunteers', reverse_lazy('dssgmkt:volunteer_list') if include_link else None)

def my_profile_link(user_pk, include_link=True):
    return ("My profile" , reverse('dssgmkt:user_profile', args=[user_pk]) if include_link else None)

def edit_my_skills_link(user_pk, include_link=True):
    return ("Edit my skills" , reverse('dssgmkt:user_profile_skills_edit', args=[user_pk]) if include_link else None)

def change_password_breadcrumb():
    return build_breadcrumb([home_link(),
                             users_link(),
                             ('My profile', reverse_lazy('dssgmkt:my_user_profile')),
                             ('Change password', None)])

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('dssgmkt:home'))

def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None

def get_url_for_notification(source_type, source_id):
    url = None
    if source_id:
        if source_type == NotificationSource.GENERIC:
            url = None
        elif source_type == NotificationSource.ORGANIZATION:
            organization = get_or_none(Organization, pk=source_id)
            if organization:
                url = reverse('dssgmkt:org_info', args=[source_id])
        elif source_type == NotificationSource.PROJECT:
            project = get_or_none(Project, pk=source_id)
            if project:
                url = reverse('dssgmkt:proj_info', args=[source_id])
        elif source_type == NotificationSource.TASK:
            project_task = get_or_none(ProjectTask, pk=source_id)
            if project_task:
                url = reverse('dssgmkt:proj_info', args=[project_task.project.id])
        elif source_type == NotificationSource.VOLUNTEER_APPLICATION:
            volunteer_application = get_or_none(VolunteerApplication, pk=source_id)
            if volunteer_application:
                url = reverse('dssgmkt:proj_volunteer_application_review', args=[volunteer_application.task.project.id, volunteer_application.task.id, source_id])
        elif source_type == NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST:
            membership_request = get_or_none(OrganizationMembershipRequest,pk=source_id)
            if membership_request:
                url = reverse('dssgmkt:org_staff_request_review', args=[membership_request.organization.id, source_id])
    return url

def volunteer_list_view(request):
    # checked_social_cause_fields = {}
    checked_awards_fields = {}
    filter_username = ""
    filter_skills = ""
    if request.method == 'POST':
        search_config = {}
        if 'username' in request.POST and request.POST.get('username'):
            search_config['username'] = request.POST.get('username')
            filter_username = request.POST.get('username')
        if 'skills' in request.POST and request.POST.get('skills'):
            search_config['skills'] = request.POST.get('skills')
            filter_skills = request.POST.get('skills')
        if 'awards' in request.POST:
            search_config['awards'] = request.POST.getlist('awards')
            for f in request.POST.getlist('awards'):
                checked_awards_fields[f] = True
        # if 'projectstatus' in request.POST:
        #     search_config['project_status'] = request.POST.getlist('projectstatus')
        #     for f in request.POST.getlist('projectstatus'):
        #         checked_project_fields[f] = True
        volunteers =  UserService.get_all_approved_volunteer_profiles(request.user, search_config)
    elif request.method == 'GET':
        volunteers =  UserService.get_all_approved_volunteer_profiles(request.user)

    if volunteers:
        volunteers_page = paginate(request, volunteers, page_size=15)
    else:
        volunteers_page = []

    return render(request, 'dssgmkt/volunteer_list.html',
                        {
                            'breadcrumb': build_breadcrumb([home_link(),
                                                          volunteers_link(include_link=False)]),
                            'leaderboards': UserService.get_volunteer_leaderboards(request.user),
                            'volunteer_list': volunteers_page,
                            # 'checked_social_cause_fields': checked_social_cause_fields,
                            'checked_awards_fields': checked_awards_fields,
                            'filter_username': filter_username,
                            'filter_skills': filter_skills,
                        })


class UserHomeView(PermissionRequiredMixin, generic.ListView): ## This is a listview because it is actually showing the list of user notifications
    model = UserNotification
    template_name = 'dssgmkt/home_user.html'
    context_object_name = 'notification_list'
    paginate_by = 10
    permission_required = 'user.is_authenticated'

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user).order_by('-notification_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = build_breadcrumb([home_link(include_link=False)])
        for notification in context['notification_list']:
            notification.url = get_url_for_notification(notification.source, notification.target_id)
        context['todos'] = UserService.get_user_todos(self.request.user, self.request.user)
        context['my_tasks'] = ProjectTaskService.get_user_in_progress_tasks(self.request.user)
        context['my_task_applications'] = ProjectTaskService.get_volunteer_open_task_applications(self.request.user, None)
        context['user_is_volunteer'] = UserService.user_has_volunteer_profile(self.request.user)
        context['user_is_any_organization_member'] = OrganizationService.user_is_any_organization_member(self.request.user)
        organizations = OrganizationService.get_organizations_with_user_create_project_permission(self.request.user)
        if len(organizations) == 1:
            context['single_org_membership'] = organizations[0]
        else:
            context['organization_memberships'] = organizations
        return context

    def render_to_response(self, context):
        response = super().render_to_response(context)
        # This should be done in the service itself but only the view knows the
        # items that are actually displayed (as pagination is done in the view) so
        # the service iteslf cannot just mark the right notifications as read.
        mark_notifications_as_read = lambda response: NotificationService.mark_notifications_as_read(context['notification_list'])
        response.add_post_render_callback(mark_notifications_as_read)
        return response

def home_view(request):
    # if request.user.is_authenticated:
    #     return UserHomeView.as_view()(request)
    # else:
    featured_volunteer = UserService.get_featured_volunteer()
    if featured_volunteer:
        featured_volunteer_skills = featured_volunteer.user.volunteerskill_set.filter(level=SkillLevel.EXPERT)
        featured_volunteer_skill_names = [volunteer_skill.skill.name for volunteer_skill in featured_volunteer_skills]
    else:
        featured_volunteer_skill_names = None
    return render(request, 'dssgmkt/home_anonymous.html',
        {
            'user_is_any_organization_member': OrganizationService.user_is_any_organization_member(request.user),
            'featured_project': ProjectService.get_featured_project(),
            'featured_organization': OrganizationService.get_featured_organization(),
            'featured_volunteer': featured_volunteer,
            'featured_volunteer_skills': featured_volunteer_skill_names,
            'news': NewsService.get_latest_news(request.user),
        })


def my_user_profile_view(request):
    return HttpResponseRedirect(reverse('dssgmkt:user_profile', args=[request.user.id]))

class UserProfileView(generic.DetailView):
    model = User
    pk_url_kwarg = 'user_pk'
    template_name = 'dssgmkt/user_profile.html'
    context_object_name = 'userprofile'

    def get_object(self):
        return UserService.get_user(self.request.user, self.kwargs['user_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = build_breadcrumb([home_link(),
                                                    users_link(),
                                                    my_profile_link(self.object.id, include_link=False) if self.object.id == self.request.user.id else (self.object.standard_display_name(), None)])

        project_tasks = ProjectTaskService.get_volunteer_all_tasks(self.request.user, self.object)
        context['project_tasks'] = paginate(self.request, project_tasks, request_key='project_tasks_page', page_size=15)
        context['pinned_reviews'] = ProjectTaskService.get_pinned_task_reviews(self.request.user, self.object)
        return context

class UserProfileEdit(PermissionRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email', 'profile_image_file', 'phone_number', 'skype_name' ]
    template_name = 'dssgmkt/user_profile_edit.html'
    pk_url_kwarg = 'user_pk'
    permission_required = 'user.is_same_user'
    raise_exception = True

    def get_success_url(self):
        return reverse('dssgmkt:user_profile', args=[self.kwargs['user_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        userprofile = get_object_or_404(User, pk=self.kwargs['user_pk'])
        context['userprofile'] = userprofile
        context['breadcrumb'] = build_breadcrumb([home_link(),
                                                  my_profile_link(self.kwargs['user_pk']),
                                                  ("Edit profile", None)])
        return context

    def form_valid(self, form):
        user = form.save(commit = False)
        try:
            UserService.save_user(self.request.user, self.kwargs['user_pk'], user)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as v:
            form.add_error(None, str(v))
            return super().form_invalid(form)

class VolunteerProfileEdit(PermissionRequiredMixin, UpdateView):
    model = VolunteerProfile
    fields = ['portfolio_url', 'github_url', 'linkedin_url', 'degree_name', 'degree_level',
              'university', 'cover_letter', 'weekly_availability_hours', 'availability_start_date',
              'availability_end_date']
    template_name = 'dssgmkt/user_volunteer_profile_edit.html'
    pk_url_kwarg = 'volunteer_pk'
    permission_required = 'user.is_same_user'
    raise_exception = True

    def get_success_url(self):
        return reverse('dssgmkt:user_profile', args=[self.kwargs['user_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        volunteerprofile = self.object
        if volunteerprofile and volunteerprofile.user.id == self.request.user.id and self.request.user.id == self.kwargs['user_pk']:
            context['volunteerprofile'] = volunteerprofile
            context['breadcrumb'] = build_breadcrumb([home_link(),
                                                        my_profile_link(volunteerprofile.user.id),
                                                        ("Edit volunteer information", None)])
            return context
        else:
            raise Http404

    def form_valid(self, form):
        volunteer_profile = form.save(commit = False)
        try:
            UserService.save_volunteer_profile(self.request.user, self.kwargs['volunteer_pk'], volunteer_profile)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as v:
            form.add_error(None, str(v))
            return super().form_invalid(form)

    def get_permission_object(self):
        return UserService.get_user(self.request.user, self.kwargs['user_pk'])


@permission_required('user.is_same_user', raise_exception=True, fn=objectgetter(User, 'user_pk'))
def user_profile_skills_edit_view(request, user_pk):
    if request.method == 'POST':
        try:
            UserService.set_volunteer_skills(request.user, user_pk, request.POST)
            return redirect('dssgmkt:user_profile', user_pk=user_pk)
        except KeyError:
            raise Http404
        except ValueError:
            pass
    elif request.method == 'GET':
        pass

    return render(request, 'dssgmkt/user_profile_skills_edit.html',
                        {
                            'breadcrumb': build_breadcrumb([home_link(),
                                                            my_profile_link(user_pk),
                                                            edit_my_skills_link(user_pk, include_link=False)]),
                            'system_skills': UserService.get_volunteer_skills(request.user, user_pk),
                            'skill_levels': UserService.get_skill_levels()
                        })


@permission_required('user.is_same_user', raise_exception=True, fn=objectgetter(User, 'user_pk'))
def create_volunteer_profile_view(request, user_pk):
    if request.method == 'GET':
        raise Http404
    elif request.method == 'POST':
        try:
            volunteer_profile = UserService.create_volunteer_profile(request.user, user_pk)
            return redirect('dssgmkt:user_volunteer_profile_edit', user_pk=user_pk, volunteer_pk=volunteer_profile.id)
        except KeyError:
            messages.error(request, 'There was an error while processing your request.')
            return redirect('dssgmkt:user_profile', user_pk=user_pk)


def select_user_type_view(request):
    return render(request, 'dssgmkt/signup_type_select.html',
                        {
                            'breadcrumb': [home_link(), ('Select your account type', None)]
                        })

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2',
                  'first_name', 'last_name', 'email', 'phone_number', 'skype_name',
                  'special_code']

def signup(request, user_type=None):
    if not user_type in ['volunteer', 'organization']:
        raise Http404
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            try:
                new_user = UserService.create_user(request.user, new_user, user_type, request.POST.get('g-recaptcha-response'))
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                login(request, user)
                messages.info(request, 'Welcome to DSSG Solve! Your account was created successfully.')
                return redirect('dssgmkt:home')
            except KeyError as k:
                form.add_error(None, str(k))
            except ValueError as v:
                form.add_error(None, str(v))
    else:
        form = SignUpForm()
    return render(request, 'dssgmkt/signup.html',
                    {
                        'form': form,
                        'user_type': user_type,
                        'breadcrumb': build_breadcrumb([home_link(),
                                                        ('Sign up', None)]),
                        'captcha_site_key': settings.RECAPTCHA_SITE_KEY,
                    })
