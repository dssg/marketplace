from datetime import timedelta

from allauth.account.models import EmailAddress
from allauth.account.utils import perform_login
from allauth.socialaccount import providers
from allauth.socialaccount.views import ConnectionsView

import django.contrib.auth.forms
import django.contrib.auth.views
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic.edit import UpdateView
from rules.contrib.views import (
    PermissionRequiredMixin, objectgetter, permission_required,
)

from ..models.org import Organization, OrganizationMembershipRequest
from ..models.proj import Project, ProjectStatus, ProjectTask, VolunteerApplication
from ..models.user import SkillLevel, User, UserType, VolunteerProfile, UserNotification, NotificationSource
from .common import build_breadcrumb, home_link, paginate

from marketplace import utils
from marketplace.domain import marketplace
from marketplace.domain.user import UserService
from marketplace.domain.proj import ProjectService, ProjectTaskService
from marketplace.domain.org import OrganizationService
from marketplace.domain.notifications import NotificationService
from marketplace.domain.news import NewsService


def dashboard_link(include_link=True):
    return ('Dashboard', reverse_lazy('marketplace:user_dashboard') if include_link else None)

def users_link(include_link=True):
    return ('Users', reverse_lazy('marketplace:volunteer_list') if include_link else None)

def volunteers_link(include_link=True):
    return ('Volunteers', reverse_lazy('marketplace:volunteer_list') if include_link else None)

def my_profile_link(user_pk, include_link=True):
    return ("My profile" , reverse('marketplace:user_profile', args=[user_pk]) if include_link else None)

def edit_my_skills_link(user_pk, include_link=True):
    return ("Edit my skills" , reverse('marketplace:user_profile_skills_edit', args=[user_pk]) if include_link else None)

def edit_my_preferences_link(user_pk, include_link=True):
    return ("Edit my interests" , reverse('marketplace:user_preferences_edit', args=[user_pk]) if include_link else None)


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
                url = reverse('marketplace:org_info', args=[source_id])
        elif source_type == NotificationSource.PROJECT:
            project = get_or_none(Project, pk=source_id)
            if project:
                url = reverse('marketplace:proj_info', args=[source_id])
        elif source_type == NotificationSource.TASK:
            project_task = get_or_none(ProjectTask, pk=source_id)
            if project_task:
                url = reverse('marketplace:proj_info', args=[project_task.project.id])
        elif source_type == NotificationSource.VOLUNTEER_APPLICATION:
            volunteer_application = get_or_none(VolunteerApplication, pk=source_id)
            if volunteer_application:
                url = reverse('marketplace:proj_volunteer_application_review', args=[volunteer_application.task.project.id, volunteer_application.task.id, source_id])
        elif source_type == NotificationSource.ORGANIZATION_MEMBERSHIP_REQUEST:
            membership_request = get_or_none(OrganizationMembershipRequest,pk=source_id)
            if membership_request:
                url = reverse('marketplace:org_staff_request_review', args=[membership_request.organization.id, source_id])
    return url


class AuthenticationForm(django.contrib.auth.forms.AuthenticationForm):

    error_messages = {
        'invalid_login': "Please enter a correct username (or email) and password. "
                         "Note that both fields may be case-sensitive.",
    }

    username = django.contrib.auth.forms.UsernameField(
        label='Username or email',
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True}),
    )


class LoginView(django.contrib.auth.views.LoginView):

    # NOTE: The below override is necessary to adopt allauth's post-
    # NOTE: login email-verification scheme.
    #
    # NOTE: allauth was added after-the-fact, for its handling of social
    # NOTE: auth; and, its LoginView assumes (for example) that you're
    # NOTE: using the url name "account_signup" as well.
    #
    # NOTE: It might make sense to switch over to its accounts-handling
    # NOTE: whole-hog; but, until then, this kind of patchwork is
    # NOTE: necessary. (And, it might not be so bad, in so far as this
    # NOTE: way we adopt only what we need.)

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        return perform_login(
            self.request,
            form.get_user(),
            email_verification=settings.ACCOUNT_EMAIL_VERIFICATION,
            redirect_url=self.get_success_url(),
        )


login_view = LoginView.as_view(
    form_class=AuthenticationForm,
    template_name='marketplace/login.html',
)


def logout_view(request):
    logout(request)
    return redirect('marketplace:home')


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

    return render(request, 'marketplace/volunteer_list.html',
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
    template_name = 'marketplace/home_user.html'
    context_object_name = 'notification_list'
    paginate_by = 10
    permission_required = 'user.is_authenticated'

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user).order_by('-notification_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = build_breadcrumb([home_link(), dashboard_link(include_link=False)])
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
    # featured volunteer
    featured_volunteer = UserService.get_featured_volunteer()
    if featured_volunteer:
        featured_volunteer_skills = (
            featured_volunteer.user.volunteerskill_set
            .filter(level=SkillLevel.EXPERT)
            .values_list('skill__name', flat=True)
        )
    else:
        featured_volunteer_skills = None

    # platform stats
    avg_days_month = 365.25 / 12
    one_avg_month = timedelta(days=avg_days_month)
    one_avg_month_ago = timezone.now() - one_avg_month

    return render(request, 'marketplace/home_anonymous.html', {
        'user_is_any_organization_member': OrganizationService.user_can_create_projects(request.user),
        'featured_project': ProjectService.get_featured_project(),
        'featured_organization': OrganizationService.get_featured_organization(),
        'featured_volunteer': featured_volunteer,
        'featured_volunteer_skills': featured_volunteer_skills,
        'news': NewsService.get_latest_news(request.user),
        'platform_stats': {
            'projects_in_design': Project.objects.filter(status=ProjectStatus.DESIGN).count(),
            'projects_this_month': Project.objects.filter(creation_date__gte=one_avg_month_ago).count(),
            'volunteers_this_month': VolunteerProfile.objects.filter(creation_date__gte=one_avg_month_ago).count(),
        },
    })


@login_required
def my_user_profile_view(request):
    return redirect('marketplace:user_profile', request.user.pk)


class UserProfileView(generic.DetailView):

    model = User
    pk_url_kwarg = 'user_pk'
    template_name = 'marketplace/user_profile.html'
    context_object_name = 'userprofile'

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
    template_name = 'marketplace/user_profile_edit.html'
    pk_url_kwarg = 'user_pk'
    permission_required = 'user.is_same_user'
    raise_exception = True

    def get_success_url(self):
        return reverse('marketplace:user_profile', args=[self.kwargs['user_pk']])

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
            return redirect(self.get_success_url())
        except ValueError as v:
            form.add_error(None, str(v))
            return super().form_invalid(form)

class VolunteerProfileEdit(PermissionRequiredMixin, UpdateView):

    model = VolunteerProfile
    fields = ('portfolio_url', 'github_url', 'linkedin_url', 'degree_name', 'degree_level',
              'university', 'cover_letter', 'weekly_availability_hours', 'availability_start_date',
              'availability_end_date')

    template_name = 'marketplace/user_volunteer_profile_edit.html'

    pk_url_kwarg = 'volunteer_pk'

    permission_required = 'user.is_same_user'
    raise_exception = True

    def get_success_url(self):
        return reverse('marketplace:user_profile', args=[self.kwargs['user_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            volunteerprofile=self.object,
            breadcrumb=build_breadcrumb([home_link(),
                                         my_profile_link(self.object.user.id),
                                         ("Edit volunteer information", None)]),
        )

        return context

    def form_valid(self, form):
        profile = form.save(commit=False)

        try:
            UserService.save_volunteer_profile(
                self.request.user,
                self.kwargs['volunteer_pk'],
                profile,
            )
        except ValueError as exc:
            form.add_error(None, str(exc))
            return super().form_invalid(form)
        else:
            self.object = profile
            return redirect(self.get_success_url())

    def get_permission_object(self):
        # NOTE: This method is called by dispatch; and,
        # get_object() isn't called -- and self.object not set
        # -- until *after* dispatch.
        # (Therefore, we can't simply return ``self.object.user``.)
        #
        # NOTE: Regardless, we're only really concerned with the User
        # owning the VolunteerProfile, (rather than the profile itself),
        # so we'll just retrieve that here -- at the same time as
        # we *enforce the consistency of the parameters in the URL*
        # (otherwise we're just testing that the user knows their ID,
        # not that they actually own this profile):
        return get_object_or_404(
            User,
            pk=self.kwargs['user_pk'],
            volunteerprofile=self.kwargs['volunteer_pk'],
        )


@permission_required('user.is_same_user', raise_exception=True, fn=objectgetter(User, 'user_pk'))
def user_preferences_edit_view(request, user_pk):
    userprofile = get_object_or_404(User, pk=user_pk)
    if request.method == 'POST':
        try:
            marketplace.user.set_task_preferences(userprofile, request.POST.getlist('preferences'))
            return redirect('marketplace:user_profile', user_pk=user_pk)
        except KeyError:
            raise Http404
        except ValueError:
            pass
    elif request.method == 'GET':
        pass
    context = {
        'breadcrumb': build_breadcrumb([home_link(),
                                        my_profile_link(user_pk),
                                        edit_my_preferences_link(user_pk, include_link=False)]),
        'userprofile': userprofile,
    }
    for p in userprofile.usertaskpreference_set.all():
        if p.is_type_scoping():
            context['has_scoping_preference'] = True
        elif p.is_type_project_management():
            context['has_project_management_preference'] = True
        elif p.is_type_domain_work():
            context['has_domain_work_preference'] = True
        elif p.is_type_qa():
            context['has_qa_preference'] = True

    return render(request, 'marketplace/user_preferences_edit.html', context)

@permission_required('user.is_same_user', raise_exception=True, fn=objectgetter(User, 'user_pk'))
def user_profile_skills_edit_view(request, user_pk):
    if request.method == 'POST':
        try:
            UserService.set_volunteer_skills(request.user, user_pk, request.POST)
            return redirect('marketplace:user_profile', user_pk=user_pk)
        except KeyError:
            raise Http404
        except ValueError:
            pass
    elif request.method == 'GET':
        pass

    return render(request, 'marketplace/user_profile_skills_edit.html',
                        {
                            'breadcrumb': build_breadcrumb([home_link(),
                                                            my_profile_link(user_pk),
                                                            edit_my_skills_link(user_pk, include_link=False)]),
                            'system_skills': UserService.get_volunteer_skills(request.user, user_pk),
                            'skill_levels': UserService.get_skill_levels()
                        })


@require_POST
@permission_required('user.is_same_user', raise_exception=True, fn=objectgetter(User, 'user_pk'))
def create_volunteer_profile_view(request, user_pk):
    volunteer_profile = marketplace.user.volunteer.ensure_profile(request.user)
    return redirect('marketplace:user_volunteer_profile_edit',
                    user_pk=user_pk, volunteer_pk=volunteer_profile.pk)


def select_user_type_before(request):
    return render(request, 'marketplace/signup_type_select.html', {
        'breadcrumb': [home_link(), ('Select your account type', None)],
    })


class UserTypeSelectionForm(forms.ModelForm):

    initial_type = forms.TypedChoiceField(
        choices=[
            (value, description)
            for (value, description) in UserType.get_choices()
            if value in (UserType.VOLUNTEER, UserType.ORGANIZATION)
        ],
        widget=utils.SubmitSelect,
    )

    class Meta:
        model = User
        fields = ('initial_type',)


@require_http_methods(['GET', 'POST'])
def select_user_type_after(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Forbidden")

    if request.method == 'GET':
        redirect_path = request.GET.get('next')
    else:
        redirect_path = request.POST.get('next')
    if not redirect_path:
        redirect_path = reverse('marketplace:user_dashboard')

    if request.user.initial_type is not None:
        return redirect(redirect_path)

    if request.method == 'POST':
        form = UserTypeSelectionForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()

            preferences = request.POST.getlist('preferences')
            marketplace.user.add_user_postsave(request.user, preferences)

            messages.info(request, "Your selection has been saved.")
            return redirect(redirect_path)
    else:
        form = UserTypeSelectionForm()

    return render(request, 'marketplace/user_type_select.html', {
        'form': form,
    })


class SignUpForm(django.contrib.auth.forms.UserCreationForm):

    def _validate_unique_username(self, username):
        """(Re)-implement username uniqueness validation.

        Disallow --

            * confusion
            * trickery
            * *attempted* (but unlikely) hacking of username/email-flexible log-in
            * mistakes

        -- reject a username:

            * equal to any existing username (*case-insensitive*)
            * equal to any registered email address (case-insensitive)

        """
        if (
            User.objects.filter(username__iexact=username).exists() or
            User.objects.filter(email__iexact=username).exists() or
            EmailAddress.objects.filter(email__iexact=username).exists()
        ):
            raise forms.ValidationError("A user with that username already exists.")

    def validate_unique(self):
        """Call the instance's validate_unique() method and update the form's
        validation errors if any were raised.

        Overridden to reimplement username uniqueness check, to prevent
        sign-up of users under confusingly-similar usernames, (either
        intentionally or not).

        (Unlike email, username is *not* otherwise considered case-
        insensitive data, and so this check is currently only
        reimplemented here.)

        """
        exclude = ['username'] + self._get_validation_exclusions()
        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as exc:
            self._update_errors(exc)

        try:
            self._validate_unique_username(self.instance.username)
        except forms.ValidationError as exc:
            self._update_errors(
                forms.ValidationError({
                    'username': [exc],
                })
            )

    class Meta:
        model = User
        fields = (
            'username',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'skype_name',
            'special_code',
        )


@require_http_methods(['GET', 'POST'])
def signup(request, user_type):
    if user_type not in ('volunteer', 'organization'):
        raise Http404

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        preferences = request.POST.getlist('preferences')

        if form.is_valid():
            try:
                if not marketplace.user.verify_captcha(
                    request.POST.get('g-recaptcha-response')
                ):
                    raise ValueError('Incorrect reCAPTCHA answer')

                marketplace.user.add_user(
                    form.save(commit=False),
                    user_type,
                    preferences,
                )  # also ValueError
            except ValueError as exc:
                form.add_error(None, str(exc))
            else:
                user = authenticate(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password1'],
                )
                messages.info(request,
                              'Welcome to DSSG Solve! '
                              'Your account was created successfully.')
                return perform_login(
                    request,
                    user,
                    email_verification=settings.ACCOUNT_EMAIL_VERIFICATION,
                    redirect_url=reverse('marketplace:user_dashboard'),
                    signup=True,  # enables a different email template;
                                  # and, for convenience, user should be
                                  # stashed in session (pending email
                                  # verification)
                )
    else:
        form = SignUpForm()
        preferences = request.GET.getlist('preferences')

    return render(request, 'marketplace/signup.html', {
        'form': form,
        'user_type': user_type,
        'breadcrumb': build_breadcrumb([home_link(), ('Sign up', None)]),
        'captcha_site_key': settings.RECAPTCHA_SITE_KEY,
        'preferences': preferences,
    })


@require_POST
def signup_oauth(request, user_type, provider_id):
    """Record desired user type before redirecting visitor to OAuth
    provider.

    *This* redirect is in fact internal, but to a handler which does not
    (need to) record any such thing, (and which handler is currently
    part of allauth). The visitor will then be redirected to the
    requested OAuth provider.

    """
    if user_type not in ('volunteer', 'organization'):
        raise Http404

    try:
        provider = providers.registry.by_id(provider_id, request)
    except LookupError:
        raise Http404

    redirect_url = provider.get_login_url(request, process='login')

    request.session['oauth_signup_usertype'] = user_type
    if 'preferences' in request.POST:
        request.session['oauth_signup_preferences'] = request.POST.getlist('preferences')

    return redirect(redirect_url)


class BasePasswordChangeView(django.contrib.auth.views.PasswordChangeView):

    success_message = None
    template_name = None

    success_url = reverse_lazy('marketplace:my_user_profile')

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        user_redirect = self.user_redirect(self.request.user)
        if user_redirect is not None:
            return user_redirect

        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def user_redirect(self, user):
        return None


class PasswordChangeView(BasePasswordChangeView):

    success_message = 'Password successfully changed.'
    template_name = 'marketplace/user_pwd_change.html'

    def user_redirect(self, user):
        if not user.has_usable_password():
            return redirect('marketplace:user_pwd_set')

change_password = PasswordChangeView.as_view(
    extra_context={
        'breadcrumb': build_breadcrumb([
            home_link(),
            ('My profile', reverse_lazy('marketplace:my_user_profile')),
            ('Change password', None),
        ]),
    },
)


class PasswordSetView(BasePasswordChangeView):

    form_class = django.contrib.auth.forms.SetPasswordForm
    template_name = 'marketplace/user_pwd_set.html'
    success_message = 'Password successfully set.'

    def user_redirect(self, user):
        if self.request.user.has_usable_password():
            return redirect('marketplace:user_pwd_change')

set_password = PasswordSetView.as_view(
    extra_context={
        'breadcrumb': build_breadcrumb([
            home_link(),
            ('My profile', reverse_lazy('marketplace:my_user_profile')),
            ('Set password', None),
        ]),
    },
)


social_connections = login_required(
    ConnectionsView.as_view(
        success_url=reverse_lazy('marketplace:user_social_connections'),
        template_name='marketplace/connections.html',
        extra_context={
            'breadcrumb': build_breadcrumb([
                home_link(),
                ('My profile', reverse_lazy('marketplace:my_user_profile')),
                ('Social accounts', None),
            ]),
            'SITE_NAME': settings.SITE_NAME,
        },
    )
)
