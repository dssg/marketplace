from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.paginator import Paginator
from django.forms import ModelForm, CharField, Textarea
from django.db.models import Case, When, Q
from django.core.exceptions import ValidationError
from django.contrib.auth import logout
from django.contrib.messages.views import SuccessMessageMixin
from datetime import date

from .models import (Organization, Project, OrganizationRole,
                    OrganizationMembershipRequest, NEW, ORGANIZATION_STAFF,
                    ACCEPTED, REJECTED, User, VolunteerProfile, ProjectTask,
                    Skill, VolunteerSkill, ProjectLog, ProjectTaskReview,
                    ProjectTaskRole, VolunteerApplication, ProjectTaskRequirement,
                    ProjectRole, ProjectFollower)
from itertools import repeat, zip_longest
from .authorization import is_organization_admin
from rules.contrib.views import permission_required, objectgetter, PermissionRequiredMixin

def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'dssgmkt/home_user.html')
    else:
        return render(request, 'dssgmkt/home_anonymous.html')

def about_view(request):
    return render(request, 'dssgmkt/about.html')

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('dssgmkt:home'))
    # Redirect to a success page.


def home_link(include_link=True):
    return ('Home', reverse('dssgmkt:home') if include_link else None)

def organizations_link(include_link=True):
    return ('Organizations', reverse('dssgmkt:org_list') if include_link else None)

def projects_link(include_link=True):
    return ('Projects', reverse('dssgmkt:proj_list') if include_link else None)


def build_breadcrumb(elements):
    return [val for pair in zip_longest(elements, repeat((' > ', None), len(elements) - 1)) for val in pair if val is not None]


class OrganizationIndexView(generic.ListView):
    template_name = 'dssgmkt/org_list.html'
    context_object_name = 'org_list'
    paginate_by = 1

    def get_queryset(self):
        return Organization.objects.order_by('-name')[:50]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = build_breadcrumb([home_link(),
                                                  organizations_link(False)])
        return context

def add_organization_user_context(context,user,organization):
    if not user.is_anonymous:
        context['user_is_staff'] = user.is_organization_staff(organization)
        context['user_is_administrator'] = user.is_organization_admin(organization)
        context['user_is_member'] = user.is_organization_member(organization)
    return context

class OrganizationView(generic.DetailView):
    model = Organization
    template_name = 'dssgmkt/org_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization_tab'] = 'info'
        context['breadcrumb'] = build_breadcrumb([home_link(),
                                                  organizations_link(),
                                                  (context['organization'].name , None)])

        projects_page_size = 1
        projects = self.object.project_set.all()
        projects_paginator = Paginator(projects, projects_page_size)
        projects_page = projects_paginator.get_page(self.request.GET.get('projects_page', 1))
        context['projects'] = projects_page
        add_organization_user_context(context, self.request.user, self.object)

        return context

class OrganizationEdit(PermissionRequiredMixin, UpdateView):
    model = Organization
    fields = '__all__'
    template_name = 'dssgmkt/org_info_edit.html'
    pk_url_kwarg = 'org_pk'
    permission_required = 'organization.information_edit'

    def get_success_url(self):
        return reverse('dssgmkt:org_info', args=[self.kwargs['org_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = get_object_or_404(Organization, pk=self.kwargs['org_pk'])
        context['organization'] = organization
        context['breadcrumb'] = organization_breadcrumb(organization,
                                                        ('Edit information', None))
        context['organization_tab']='info'
        return context

def organization_breadcrumb(organization, *items):
    breadcrumb_items = [home_link(),
                        organizations_link(),
                        (organization.name , reverse('dssgmkt:org_info', args=[organization.id]) if items[0] else None)]
    breadcrumb_items += items
    return build_breadcrumb(breadcrumb_items)

class CreateOrganizationRoleForm(ModelForm):
    class Meta:
        model = OrganizationRole
        fields = ['role', 'user']

@permission_required('organization.staff_view', fn=objectgetter(Organization, 'pk'))
def organization_staff_view(request, pk):
    if request.method == 'GET':
        organization = get_object_or_404(Organization, pk=pk)
        staff_page_size = 50
        organization_staff = organization.organizationrole_set.all().order_by('role')
        staff_paginator = Paginator(organization_staff, staff_page_size)
        staff_page = staff_paginator.get_page(request.GET.get('staff_page', 1))

        requests_page_size = 50
        organization_requests = organization.organizationmembershiprequest_set.all().order_by(
                Case(When(status=NEW, then=0),
                     When(status=ACCEPTED, then=1),
                     When(status=REJECTED, then=2)), '-request_date')
        requests_paginator = Paginator(organization_requests, requests_page_size)
        requests_page = requests_paginator.get_page(request.GET.get('requests_page', 1))

        return render(request, 'dssgmkt/org_staff.html',
                        add_organization_user_context(
                            {'organization': organization,
                            'organization_tab': 'staff',
                            'breadcrumb': organization_breadcrumb(organization, ('Staff', None)),

                            'organization_staff': staff_page,

                            'organization_requests': requests_page,

                            'add_staff_form': CreateOrganizationRoleForm(),
                            }, request.user, organization))
    ## TODO this is a security hole as staff can post to this view and create new members
    elif request.method == 'POST':
        form = CreateOrganizationRoleForm(request.POST)
        if form.is_valid:
            organization_role = form.save(commit = False)
            organization = get_object_or_404(Organization, pk=pk)
            organization_role.organization = organization
            organization_role.save()
            return redirect('dssgmkt:org_staff', pk = pk)


class OrganizationMembershipRequestCreate(CreateView):
    model = OrganizationMembershipRequest
    fields = []
    template_name = 'dssgmkt/org_staff_request.html'

    def get_success_url(self):
        return reverse('dssgmkt:org_info', args=[self.kwargs['org_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = get_object_or_404(Organization, pk=self.kwargs['org_pk'])
        context['organization'] = organization
        context['breadcrumb'] = organization_breadcrumb(organization,
                                                        ('Request membership', None))
        context['organization_tab']='info'
        return context


    def form_valid(self, form):
        membership_request = form.save(commit=False)
        organization = get_object_or_404(Organization, pk=self.kwargs['org_pk'])
        membership_request.organization = organization
        membership_request.user = self.request.user
        membership_request.status = NEW
        membership_request.role = ORGANIZATION_STAFF
        membership_request.save()
        return HttpResponseRedirect(self.get_success_url())


class OrganizationMembershipRequestForm(ModelForm):
    class Meta:
        model = OrganizationMembershipRequest
        fields = ['role', 'status', 'public_reviewer_comments', 'private_reviewer_notes']

    def clean_status(self):
        status = self.cleaned_data['status']
        if status == NEW:
            raise ValidationError("Please mark this membership request as accepted or rejected")
        return status
    #
    # def __init__(self, *args, **kwargs):
    #     super(OrganizationMembershipRequestForm, self).__init__(*args, **kwargs)
    #     self.fields['status'].queryset = None

class OrganizationMembershipRequestEdit(PermissionRequiredMixin, UpdateView):
    model = OrganizationMembershipRequest
    form_class = OrganizationMembershipRequestForm
    template_name = 'dssgmkt/org_staff_request_review.html'
    pk_url_kwarg = 'request_pk'
    permission_required = 'organization.membership_review'

    def get_success_url(self):
        return reverse('dssgmkt:org_staff', args=[self.kwargs['org_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = get_object_or_404(Organization, pk=self.kwargs['org_pk'])
        membership_request = self.object
        if membership_request and membership_request.organization.id == self.kwargs['org_pk']:
            context['organization'] = organization
            context['breadcrumb'] = organization_breadcrumb(organization,
                                                            ('Staff', reverse('dssgmkt:org_staff', args=[self.object.organization.id])),
                                                            ('Review membership request', None))
            context['organization_tab']='staff'
            return context
        else:
            raise Http404

class OrganizationRoleEdit(PermissionRequiredMixin, UpdateView):
    model = OrganizationRole
    fields = ['role']
    template_name = 'dssgmkt/org_staff_edit.html'
    pk_url_kwarg = 'role_pk'
    permission_required = 'organization.role_edit'

    def get_success_url(self):
        return reverse('dssgmkt:org_staff', args=[self.object.organization.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization_role = self.object
        if organization_role and organization_role.organization.id == self.kwargs['org_pk']:
            context['organization'] = self.object.organization
            context['breadcrumb'] = organization_breadcrumb(self.object.organization,
                                                            ('Staff', reverse('dssgmkt:org_staff', args=[self.object.organization.id])),
                                                            ('Edit', None))
            context['organization_tab']='staff'
            return context
        else:
            raise Http404



class OrganizationLeave(PermissionRequiredMixin, DeleteView):
    model = OrganizationRole
    template_name = 'dssgmkt/org_staff_leave.html'
    permission_required = 'organization.membership_leave'

    def get_object(self):
        return get_object_or_404(OrganizationRole, organization=self.kwargs['org_pk'], user=self.request.user.id)

    def get_success_url(self):
        return reverse('dssgmkt:org_info', args=[self.object.organization.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization_role = self.object
        if organization_role and organization_role.organization.id == self.kwargs['org_pk']:
            context['organization'] = self.object.organization
            context['breadcrumb'] = organization_breadcrumb(self.object.organization,
                                                            ('Leave organization', None))
            context['organization_tab']='info'
            return context
        else:
            raise Http404

class OrganizationRoleRemove(PermissionRequiredMixin, DeleteView):
    model = OrganizationRole
    template_name = 'dssgmkt/org_staff_remove.html'
    pk_url_kwarg = 'role_pk'
    permission_required = 'organization.role_delete'

    def get_success_url(self):
        return reverse('dssgmkt:org_staff', args=[self.object.organization.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization_role = self.object
        if organization_role and organization_role.organization.id == self.kwargs['org_pk']:
            context['organization'] = self.object.organization
            context['breadcrumb'] = organization_breadcrumb(self.object.organization,
                                                            ('Staff', reverse('dssgmkt:org_staff', args=[self.object.organization.id])),
                                                            ('Remove', None))
            context['organization_tab']='staff'
            return context
        else:
            raise Http404

def my_user_profile_view(request):
    return HttpResponseRedirect(reverse('dssgmkt:user_profile', args=[request.user.id]))

class UserProfileView(generic.DetailView):
    model = User
    pk_url_kwarg = 'user_pk'
    template_name = 'dssgmkt/user_profile.html'
    context_object_name = 'userprofile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = build_breadcrumb([home_link(),
                                                  ("My profile" , None)])

        project_tasks_page_size = 1
        project_tasks = ProjectTask.objects.filter(projecttaskrole__user=self.object.id).filter(~Q(project__status = Project.DRAFT))
        project_tasks_paginator = Paginator(project_tasks, project_tasks_page_size)
        project_tasks_page = project_tasks_paginator.get_page(self.request.GET.get('project_tasks_page', 1))
        context['project_tasks'] = project_tasks_page

        return context

class UserProfileEdit(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'skype_name' ]
    template_name = 'dssgmkt/user_profile_edit.html'
    pk_url_kwarg = 'user_pk'

    def get_success_url(self):
        return reverse('dssgmkt:user_profile', args=[self.kwargs['user_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        userprofile = get_object_or_404(User, pk=self.kwargs['user_pk'])
        context['userprofile'] = userprofile
        context['breadcrumb'] = build_breadcrumb([home_link(),
                                                  ("My profile" , reverse('dssgmkt:user_profile', args=[userprofile.id])),
                                                  ("Edit profile", None)])
        return context

class VolunteerProfileEdit(UpdateView):
    model = VolunteerProfile
    fields = ['portfolio_url', 'github_url', 'linkedin_url', 'degree_name', 'degree_level',
              'university', 'cover_letter', 'weekly_availability_hours', 'availability_start_date',
              'availability_end_date']
    template_name = 'dssgmkt/user_volunteer_profile_edit.html'
    pk_url_kwarg = 'volunteer_pk'

    def get_success_url(self):
        return reverse('dssgmkt:user_profile', args=[self.kwargs['user_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        volunteerprofile = self.object
        if volunteerprofile and volunteerprofile.user.id == self.request.user.id and self.request.user.id == self.kwargs['user_pk']:
            context['volunteerprofile'] = volunteerprofile
            context['breadcrumb'] = build_breadcrumb([home_link(),
                                                      ("My profile" , reverse('dssgmkt:user_profile', args=[volunteerprofile.user.id])),
                                                      ("Edit volunteer information", None)])
            return context
        else:
            raise Http404

class CreateSkillForm(ModelForm):
    class Meta:
        model = VolunteerSkill
        fields = ['skill', 'level']

def user_profile_skills_edit_view(request, user_pk):
    if request.method == 'GET':
        volunteerskills = VolunteerSkill.objects.filter(user__id = user_pk)

        return render(request, 'dssgmkt/user_profile_skills_edit.html',
                            {'volunteerskills': volunteerskills,
                            'breadcrumb': build_breadcrumb([home_link(),
                                                              ("My profile" , reverse('dssgmkt:user_profile', args=[user_pk])),
                                                              ("Edit skills", None)]),

                            'add_skill_form': CreateSkillForm(),
                            })
    ## TODO this is a security hole as anybody can post to this view and create new skills
    elif request.method == 'POST':
        form = CreateSkillForm(request.POST)
        if form.is_valid:
            skill = form.save(commit = False)
            skill.user = request.user
            skill.save()
            return redirect('dssgmkt:user_profile_skills_edit', user_pk = user_pk)

class VolunteerSkillEdit(UpdateView):
    model = VolunteerSkill
    fields = ['level']
    template_name = 'dssgmkt/user_profile_skills_skill_edit.html'
    pk_url_kwarg = 'skill_pk'

    def get_success_url(self):
        return reverse('dssgmkt:user_profile_skills_edit', args=[self.object.user.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        volunteer_skill = self.object
        if volunteer_skill and volunteer_skill.user.id == self.request.user.id and self.request.user.id == self.kwargs['user_pk']:
            context['volunteerskill'] = volunteer_skill
            context['breadcrumb'] =  build_breadcrumb([home_link(),
                                                      ("My profile" , reverse('dssgmkt:user_profile', args=[self.kwargs['user_pk']])),
                                                      ("Edit skills", reverse('dssgmkt:user_profile_skills_edit', args=[self.kwargs['user_pk']])),
                                                      ("Edit skill", None)])
            return context
        else:
            raise Http404

class VolunteerSkillRemove(DeleteView):
    model = VolunteerSkill
    template_name = 'dssgmkt/user_profile_skills_skill_remove.html'
    pk_url_kwarg = 'skill_pk'

    def get_success_url(self):
        return reverse('dssgmkt:user_profile_skills_edit', args=[self.kwargs['user_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        volunteer_skill = self.object
        if volunteer_skill and volunteer_skill.user.id == self.request.user.id and self.request.user.id == self.kwargs['user_pk']:
            context['volunteerskill'] = volunteer_skill
            context['breadcrumb'] =  build_breadcrumb([home_link(),
                                                      ("My profile" , reverse('dssgmkt:user_profile', args=[self.kwargs['user_pk']])),
                                                      ("Edit skills", reverse('dssgmkt:user_profile_skills_edit', args=[self.kwargs['user_pk']])),
                                                      ("Remove skill", None)])
            return context
        else:
            raise Http404


class ProjectIndexView(generic.ListView):
    template_name = 'dssgmkt/proj_list.html'
    context_object_name = 'proj_list'
    paginate_by = 1

    def get_queryset(self):
        return Project.objects.order_by('name')[:50]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = build_breadcrumb([home_link(),
                                                  projects_link(False)])
        return context


def project_breadcrumb(project, last_text = None):
    breadcrumb_items = [home_link(),
                        projects_link(),
                        (project.name , reverse('dssgmkt:proj_info', args=[project.id]) if last_text else None)]
    if last_text:
        breadcrumb_items.append((last_text, None))
    return build_breadcrumb(breadcrumb_items)


class ProjectView(generic.ListView): ## This is a listview because it is actually showing the list of open tasks
    model = ProjectTask
    template_name = 'dssgmkt/proj_info.html'
    context_object_name = 'project_tasks'

    def get_queryset(self):
        return ProjectTask.objects.filter(stage = ProjectTask.ACCEPTING_VOLUNTEERS,
                                          project = self.kwargs['proj_pk']).order_by('name')[:50]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk = self.kwargs['proj_pk'])
        context['project'] = project
        context['project_tab'] = 'info'
        context['breadcrumb'] = project_breadcrumb(project)
        if not self.request.user.is_anonymous:
            context['user_is_following_project'] = ProjectFollower.objects.filter(project = project, user = self.request.user).exists()
        return context

class ProjectLogView(generic.ListView):
    template_name = 'dssgmkt/proj_log.html'
    context_object_name = 'project_logs'
    paginate_by = 1

    def get_queryset(self):
        project_pk = self.kwargs['proj_pk']
        project = get_object_or_404(Project, pk = project_pk)
        return ProjectLog.objects.filter(project = project).order_by('-change_date')[:50]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs['proj_pk']
        project = get_object_or_404(Project, pk = project_pk)
        context['breadcrumb'] = project_breadcrumb(project, 'Change log')
        context['project'] = project
        context['project_tab'] = 'log'
        return context



class ProjectDeliverablesView(generic.DetailView):
    model = Project
    template_name = 'dssgmkt/proj_deliverables.html'
    pk_url_kwarg = 'proj_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_tab'] = 'deliverables'
        context['breadcrumb'] = project_breadcrumb(context['project'], 'Project deliverables')
        context['project'] = self.object
        return context

class ProjectVolunteerInstructionsView(generic.DetailView):
    model = ProjectTask
    template_name = 'dssgmkt/proj_instructions.html'
    pk_url_kwarg = 'proj_pk'

    def get_object(self):
        return ProjectTask.objects.filter(project__pk = self.kwargs['proj_pk'],
                                          projecttaskrole__user = self.request.user,
                                          stage__in=[ProjectTask.STARTED, ProjectTask.WAITING_REVIEW]).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.object:
            project_pk = self.kwargs['proj_pk']
            project = get_object_or_404(Project, pk = project_pk)
        else:
            project = self.object.project
        context['project_tab'] = 'instructions'
        context['breadcrumb'] = project_breadcrumb(project, 'Volunteer instructions')
        context['project'] = project
        context['project_task'] = self.object
        return context

class CreateProjectTaskReviewForm(ModelForm):
    class Meta:
        model = ProjectTaskReview
        fields = ['volunteer_comment', 'volunteer_effort_hours']

class ProjectTaskReviewCreate(CreateView):
    model = ProjectTaskReview
    fields = ['volunteer_comment', 'volunteer_effort_hours']
    template_name = 'dssgmkt/proj_task_finish.html'

    def get_success_url(self):
        return reverse('dssgmkt:proj_info', args=[self.kwargs['proj_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task = get_object_or_404(ProjectTask, pk=self.kwargs['task_pk'])
        context['project'] = project_task.project
        context['project_task'] = project_task
        context['breadcrumb'] = project_breadcrumb(project_task.project, 'Volunteer instructions')
        context['organization_tab']='instructions'
        return context

    def form_valid(self, form):
        project_task_review = form.save(commit=False)
        project_task = get_object_or_404(ProjectTask, pk=self.kwargs['task_pk'])
        project = get_object_or_404(Project, pk=self.kwargs['proj_pk'])
        project_task_review.task = project_task
        project_task_review.review_result = NEW
        project_task_review.save()
        project_task.stage = ProjectTask.WAITING_REVIEW
        project_task.save()
        project_task.project.status = Project.WAITING_REVIEW
        project_task.project.save()
        return HttpResponseRedirect(self.get_success_url())

class ProjectTaskCancel(DeleteView):
    model = ProjectTaskRole
    template_name = 'dssgmkt/proj_task_cancel.html'

    def get_object(self):
        return get_object_or_404(ProjectTaskRole, task=self.kwargs['task_pk'], user=self.request.user.id)

    def get_success_url(self):
        return reverse('dssgmkt:proj_info', args=[self.object.task.project.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task_role = self.object
        project_task = project_task_role.task
        project = project_task.project
        context['project_task'] = project_task
        context['project'] = project
        context['breadcrumb'] = project_breadcrumb(project, 'Stop volunteering')
        context['organization_tab']='instructions'
        return context


class ProjectTaskApply(CreateView):
    model = VolunteerApplication
    fields = ['volunteer_application_letter']
    template_name = 'dssgmkt/proj_task_apply.html'

    def get_success_url(self):
        return reverse('dssgmkt:proj_info', args=[self.kwargs['proj_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task = get_object_or_404(ProjectTask, pk=self.kwargs['task_pk'])
        project = get_object_or_404(Project, pk=self.kwargs['proj_pk'])
        context['project'] = project
        context['project_task'] = project_task
        context['breadcrumb'] = project_breadcrumb(project, 'Apply to volunteer')
        context['project_tab']='info'
        return context

    def form_valid(self, form):
        task_application_request = form.save(commit=False)
        task = get_object_or_404(ProjectTask, pk=self.kwargs['task_pk'])

        task_application_request.status = NEW
        task_application_request.task = task
        task_application_request.volunteer = self.request.user
        task_application_request.save()
        return HttpResponseRedirect(self.get_success_url())


class ProjectTaskIndex(generic.ListView):
    model = ProjectTask
    template_name = 'dssgmkt/proj_task_list.html'
    context_object_name = 'project_tasks'

    def get_queryset(self):
        return ProjectTask.objects.filter(project = self.kwargs['proj_pk']).order_by('estimated_start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk = self.kwargs['proj_pk'])
        context['project'] = project
        context['project_tab'] = 'tasklist'
        context['breadcrumb'] = project_breadcrumb(project, 'Tasks')
        return context



class ProjectTaskEdit(UpdateView):
    model = ProjectTask
    fields = ['name', 'description', 'type', 'onboarding_instructions', 'stage', 'accepting_volunteers', 'estimated_start_date',
                'estimated_end_date', 'estimated_effort_hours', 'task_home_url', 'task_deliverables_url']
    template_name = 'dssgmkt/proj_task_edit.html'
    pk_url_kwarg = 'task_pk'

    def get_success_url(self):
        return reverse('dssgmkt:proj_task_list', args=[self.kwargs['proj_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.kwargs['proj_pk'])
        context['project'] = project
        context['project_task'] = self.object
        context['breadcrumb'] = project_breadcrumb(project, 'Edit project task')
        context['project_tab']='tasklist'
        return context


class ProjectEdit(UpdateView):
    model = Project
    fields = ['name', 'short_summary', 'motivation','solution_description', 'challenges', 'banner_image_url', 'project_cause',
            'project_impact', 'scoping_process', 'available_staff', 'available_data', 'developer_agreement', 'intended_start_date',
            'intended_end_date', 'deliverable_github_url', 'deliverable_management_url', 'deliverable_documentation_url',
            'deliverable_reports_url']
    template_name = 'dssgmkt/proj_info_edit.html'
    pk_url_kwarg = 'proj_pk'

    def get_success_url(self):
        return reverse('dssgmkt:proj_info', args=[self.kwargs['proj_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.kwargs['proj_pk'])
        context['project'] = project
        context['breadcrumb'] = project_breadcrumb(project, 'Edit project information')
        context['project_tab']='info'
        return context


class CreateTaskRequirementForm(ModelForm):
    class Meta:
        model = ProjectTaskRequirement
        fields = ['skill', 'level']

def project_task_requirements_edit_view(request, proj_pk, task_pk):
    if request.method == 'GET':
        task_requirements = ProjectTaskRequirement.objects.filter(task = task_pk)
        project = get_object_or_404(Project, pk = proj_pk)
        return render(request, 'dssgmkt/proj_task_requirements_edit.html',
                            {
                            'project': project,
                            'project_task': get_object_or_404(ProjectTask, pk = task_pk),
                            'task_requirements': task_requirements,
                            'breadcrumb': project_breadcrumb(project, 'Edit project task requirements'),
                            'add_requirement_form': CreateTaskRequirementForm()
                            })
    ## TODO this is a security hole as anybody can post to this view and create new skills
    elif request.method == 'POST':
        form = CreateTaskRequirementForm(request.POST)
        if form.is_valid:
            requirement = form.save(commit = False)
            project_task = get_object_or_404(ProjectTask, pk = task_pk)
            requirement.task = project_task
            requirement.save()
            return redirect('dssgmkt:proj_task_requirements_edit', proj_pk = proj_pk, task_pk = task_pk)

class ProjectTaskRequirementEdit(UpdateView):
    model = ProjectTaskRequirement
    fields = ['level']
    template_name = 'dssgmkt/proj_task_requirements_requirement_edit.html'
    pk_url_kwarg = 'requirement_pk'

    def get_success_url(self):
        return reverse('dssgmkt:proj_task_requirements_edit', args=[self.kwargs['proj_pk'],self.kwargs['task_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_requirement = self.object
        if task_requirement:
            project_task = task_requirement.task
            project = project_task.project
            context['project'] = project
            context['project_task'] = project_task
            context['task_requirement'] = task_requirement
            context['breadcrumb'] =  project_breadcrumb(project, 'Edit project task requirement')
            return context
        else:
            raise Http404

class ProjectTaskRequirementRemove(DeleteView):
    model = ProjectTaskRequirement
    template_name = 'dssgmkt/proj_task_requirements_requirement_remove.html'
    pk_url_kwarg = 'requirement_pk'

    def get_success_url(self):
        return reverse('dssgmkt:proj_task_requirements_edit', args=[self.kwargs['proj_pk'],self.kwargs['task_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_requirement = self.object
        if task_requirement:
            project_task = task_requirement.task
            project = project_task.project
            context['project'] = project
            context['project_task'] = project_task
            context['task_requirement'] = task_requirement
            context['breadcrumb'] =  project_breadcrumb(project, 'Edit project task requirement')
            return context
        else:
            raise Http404

class ProjectTaskRemove(DeleteView):
    model = ProjectTask
    template_name = 'dssgmkt/proj_task_remove.html'
    pk_url_kwarg = 'task_pk'

    def get_success_url(self):
        return reverse('dssgmkt:proj_task_list', args=[self.kwargs['proj_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task = self.object
        if project_task:
            project = project_task.project
            context['project'] = project
            context['project_task'] = project_task
            context['breadcrumb'] =  project_breadcrumb(project, 'Delete task')
            return context
        else:
            raise Http404


def create_default_project_task(request, proj_pk):
    if request.method == 'GET':
        raise Http404
    ## TODO this is a security hole as anybody can post to this view and create new skills
    elif request.method == 'POST':
        project_task = ProjectTask()
        project_task.name = 'New project task'
        project_task.description = 'This is the task description'
        project_task.onboarding_instructions = 'These are the volunteer onboarding instructions'
        project_task.stage = ProjectTask.NOT_STARTED
        project_task.accepting_volunteers = False
        project_task.project = get_object_or_404(Project, pk = proj_pk)
        project_task.percentage_complete = 0
        project_task.business_area = 'no'
        project_task.estimated_start_date = date.today()
        project_task.estimated_end_date = date.today()
        project_task.save()
        return redirect('dssgmkt:proj_task_list', proj_pk = proj_pk)


class CreateProjectRoleForm(ModelForm):
    class Meta:
        model = ProjectRole
        fields = ['role', 'user']

def project_staff_view(request, proj_pk):
    if request.method == 'GET':
        project = get_object_or_404(Project, pk = proj_pk)
        staff_page_size = 50
        project_staff = project.projectrole_set.all().order_by('role')
        staff_paginator = Paginator(project_staff, staff_page_size)
        staff_page = staff_paginator.get_page(request.GET.get('staff_page', 1))

        volunteers_page_size = 1
        volunteers = ProjectTaskRole.objects.filter(task__project__id = proj_pk)
        volunteers_paginator = Paginator(volunteers, volunteers_page_size)
        volunteers_page = volunteers_paginator.get_page(request.GET.get('volunteers_page', 1))

        applications_page_size = 50
        volunteer_applications = VolunteerApplication.objects.filter(task__project__id = proj_pk).order_by(
                Case(When(status=NEW, then=0),
                     When(status=ACCEPTED, then=1),
                     When(status=REJECTED, then=2)), '-application_date')
        volunteer_applications_paginator = Paginator(volunteer_applications, applications_page_size)
        applications_page = volunteer_applications_paginator.get_page(request.GET.get('applications_page', 1))

        return render(request, 'dssgmkt/proj_staff.html',
                            {'project': project,
                            'project_tab': 'staff',
                            'breadcrumb': project_breadcrumb(project, 'Delete task'),

                            'project_staff': staff_page,
                            'volunteers': volunteers_page,
                            'volunteer_applications': applications_page,

                            'add_staff_form': CreateProjectRoleForm(),

                            'user_is_project_owner': True, ## TODO remove this
                            })
    ## TODO this is a security hole as staff can post to this view and create new members
    elif request.method == 'POST':
        form = CreateProjectRoleForm(request.POST)
        if form.is_valid:
            project_role = form.save(commit = False)
            project = get_object_or_404(Project, pk = proj_pk)
            project_role.project = project
            project_role.save()
            return redirect('dssgmkt:proj_staff', proj_pk = proj_pk)



class ProjectRoleEdit(SuccessMessageMixin, UpdateView):
    model = ProjectRole
    fields = ['role']
    template_name = 'dssgmkt/proj_staff_edit.html'
    pk_url_kwarg = 'role_pk'
    success_message = 'Role edited successfully'

    def get_success_url(self):
        return reverse('dssgmkt:proj_staff', args=[self.object.project.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_role = self.object
        if project_role and project_role.project.id == self.kwargs['proj_pk']:
            project = self.object.project
            context['project'] = project
            context['breadcrumb'] =  project_breadcrumb(project,
                                                        ('Staff', reverse('dssgmkt:proj_staff', args=[self.object.project.id])))
            context['project_tab'] = 'staff'
            return context
        else:
            raise Http404

class ProjectRoleRemove(DeleteView):
    model = ProjectRole
    template_name = 'dssgmkt/proj_staff_remove.html'
    pk_url_kwarg = 'role_pk'

    def get_success_url(self):
        return reverse('dssgmkt:proj_staff', args=[self.object.project.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_role = self.object
        if project_role and project_role.project.id == self.kwargs['proj_pk']:
            project = self.object.project
            context['project'] = project
            context['breadcrumb'] =  project_breadcrumb(project,
                                                        ('Staff', reverse('dssgmkt:proj_staff', args=[self.object.project.id])))
            context['project_tab']='staff'
            return context
        else:
            raise Http404

class ProjectTaskRoleRemove(DeleteView):
    model = ProjectTaskRole
    template_name = 'dssgmkt/proj_volunteer_remove.html'

    def get_object(self):
        return get_object_or_404(ProjectTaskRole, pk = self.kwargs['task_role_pk'])

    def get_success_url(self):
        return reverse('dssgmkt:proj_staff', args=[self.object.task.project.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task_role = self.object
        project_task = project_task_role.task
        project = project_task.project
        context['project_task'] = project_task
        context['project'] = project
        context['breadcrumb'] = project_breadcrumb(project, 'Remove volunteer')
        context['organization_tab']='staff'
        return context

class ProjectVolunteerApplicationEdit(UpdateView):
    model = VolunteerApplication
    fields = ['status', 'public_reviewer_comments', 'private_reviewer_notes']
    template_name = 'dssgmkt/proj_volunteer_application_review.html'
    pk_url_kwarg = 'volunteer_application_pk'

    def get_success_url(self):
        return reverse('dssgmkt:proj_staff', args=[self.kwargs['proj_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.kwargs['proj_pk'])
        volunteer_application = self.object
        if volunteer_application and volunteer_application.task.id == self.kwargs['task_pk'] and volunteer_application.task.project.id == self.kwargs['proj_pk']:
            context['project'] = project
            context['breadcrumb'] = project_breadcrumb(project, 'Review volunteer')
            context['project_tab']='staff'
            return context
        else:
            raise Http404

def follow_project_view(request, proj_pk):
    if request.method == 'GET':
        raise Http404
    ## TODO this is a security hole as anybody can post to this view and create new skills
    elif request.method == 'POST':
        project = get_object_or_404(Project, pk = proj_pk)
        project_follower = ProjectFollower.objects.filter(project = project, user = request.user).first()
        if project_follower:
            project_follower.delete()
        else:
            project_follower = ProjectFollower()
            project_follower.project = project
            project_follower.user = request.user
            project_follower.save()
        return redirect('dssgmkt:proj_info', proj_pk = proj_pk)
