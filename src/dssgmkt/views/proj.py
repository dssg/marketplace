from datetime import date

import traceback
from django.contrib.auth import logout
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import CharField, ModelForm, Textarea
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from rules.contrib.views import (
    PermissionRequiredMixin, objectgetter, permission_required,
)

from ..models.common import ReviewStatus
from ..models.proj import (
    Project, ProjectFollower, ProjectLog, ProjectComment, ProjectRole,
    ProjectTask, ProjectTaskRequirement, ProjectStatus, TaskStatus,
    ProjectTaskReview, ProjectTaskRole, VolunteerApplication, ProjectScope,
)
from .common import build_breadcrumb, home_link, paginate, generic_getter
from .org import organizations_link, organization_link, get_organization, add_organization_common_context
from dssgmkt.domain.proj import ProjectService, ProjectTaskService

from dssgmkt.domain.org import OrganizationService
from dssgmkt.domain.user import UserService

def projects_link(include_link=True):
    return ('Projects', reverse('dssgmkt:proj_list') if include_link else None)

def project_link(project, include_link=True):
    return (project.name, reverse('dssgmkt:proj_info', args=[project.id]) if include_link else None)

def staff_link(project, include_link=True):
    return ('Staff', reverse('dssgmkt:proj_staff', args=[project.id]) if include_link else None)

def volunteers_link(project, include_link=True):
    return ('Volunteers', reverse('dssgmkt:proj_volunteers', args=[project.id]) if include_link else None)

def volunteer_instructions_link(project, include_link=True):
    return ('My tasks', reverse('dssgmkt:proj_instructions', args=[project.id]) if include_link else None)

def volunteer_instructions_task_link(project_task, include_link=True):
    return (project_task.name, reverse('dssgmkt:proj_instructions_task', args=[project_task.project.id, project_task.id]) if include_link else None)

def tasks_link(project, include_link=True):
    return ('Tasks', reverse('dssgmkt:proj_task_list', args=[project.id]) if include_link else None)

def task_link(project_task, include_link=True):
    return (project_task.name, reverse('dssgmkt:proj_task', args=[project_task.project.id, project_task.id]) if include_link else None)

def edit_task_requirements_link(project, task, include_link=True):
    return ('Edit requirements', reverse('dssgmkt:proj_task_requirements_edit', args=[project.id, task.id]) if include_link else None)

def discussion_index_link(project, include_link=True):
    return ('Discussion', reverse('dssgmkt:proj_discussion', args=[project.id]) if include_link else None)

def project_breadcrumb(project, *items):
    breadcrumb_items = [home_link(),
                        projects_link(),
                        project_link(project, items)]
    breadcrumb_items += items
    return build_breadcrumb(breadcrumb_items)

def project_task_breadcrumb(project_task):
    breadcrumb_items = [home_link(),
                        projects_link(),
                        project_link(project_task.project),
                        tasks_link(project_task.project),
                        (project_task.name, None)
                        ]
    return build_breadcrumb(breadcrumb_items)

def project_volunteer_task_breadcrumb(project_task, *items):
    breadcrumb_items = [home_link(),
                        projects_link(),
                        project_link(project_task.project),
                        volunteer_instructions_link(project_task.project),
                        volunteer_instructions_task_link(project_task, items)
                        ]
    breadcrumb_items += items
    return build_breadcrumb(breadcrumb_items)

def get_project(request, proj_pk):
    return generic_getter(ProjectService.get_project, request.user, proj_pk)

def get_project_scope(request, proj_pk, scope_pk):
    return generic_getter(ProjectService.get_project_scope, request.user, proj_pk, scope_pk)

def get_project_task(request, proj_pk, task_pk):
    return generic_getter(ProjectTaskService.get_project_task,request.user, proj_pk, task_pk)

def get_project_task_role(request, proj_pk, task_pk, role_pk):
    return generic_getter(ProjectTaskService.get_project_task_role, request.user, proj_pk, task_pk, role_pk)

def get_own_project_task_role(request, proj_pk, task_pk):
    return generic_getter(ProjectTaskService.get_own_project_task_role, request.user, proj_pk, task_pk)

def get_project_task_review(request, proj_pk, task_pk, review_pk):
    return generic_getter(ProjectTaskService.get_project_task_review, request.user, proj_pk, task_pk, review_pk)

def get_project_task_requirements(request, proj_pk, task_pk):
    return ProjectTaskService.get_project_task_requirements(request.user, proj_pk, task_pk)

def get_volunteer_application(request, proj_pk, task_pk, volunteer_application_pk):
    return generic_getter(ProjectTaskService.get_volunteer_application, request.user, proj_pk, task_pk, volunteer_application_pk)

def get_project_role(request, proj_pk, role_pk):
    return generic_getter(ProjectService.get_project_role, request.user, proj_pk, role_pk)


def project_list_view(request):
    checked_social_cause_fields = {}
    checked_project_fields = {}
    filter_projname = ""
    filter_orgname = ""
    filter_skills = ""
    if request.method == 'POST':
        search_config = {}
        if 'projname' in request.POST and request.POST.get('projname'):
            search_config['projname'] = request.POST.get('projname')
            filter_projname = request.POST.get('projname')
        if 'orgname' in request.POST and request.POST.get('orgname'):
            search_config['orgname'] = request.POST.get('orgname')
            filter_orgname = request.POST.get('orgname')
        if 'skills' in request.POST and request.POST.get('skills'):
            search_config['skills'] = request.POST.get('skills')
            filter_skills = request.POST.get('skills')
        if 'socialcause' in request.POST:
            search_config['social_cause'] = request.POST.getlist('socialcause')
            for f in request.POST.getlist('socialcause'):
                checked_social_cause_fields[f] = True
        if 'projectstatus' in request.POST:
            search_config['project_status'] = request.POST.getlist('projectstatus')
            for f in request.POST.getlist('projectstatus'):
                checked_project_fields[f] = True
        projects =  ProjectService.get_all_projects(request.user, search_config)
    elif request.method == 'GET':
        projects =  ProjectService.get_all_projects(request.user)

    if projects:
        projects_page = paginate(request, projects, page_size=15)
    else:
        projects_page = []

    any_org_member = OrganizationService.user_is_any_organization_member(request.user)
    organizations = OrganizationService.get_organizations_with_user_create_project_permission(request.user)
    if len(organizations) == 1:
        single_org_membership = organizations[0]
        organization_memberships = None
    else:
        single_org_membership = None
        organization_memberships = organizations
    return render(request, 'dssgmkt/proj_list.html',
                        {
                            'breadcrumb': build_breadcrumb([home_link(), projects_link(False)]),
                            'proj_list': projects_page,
                            'checked_social_cause_fields': checked_social_cause_fields,
                            'checked_project_fields': checked_project_fields,
                            'filter_projname': filter_projname,
                            'filter_orgname': filter_orgname,
                            'filter_skills': filter_skills,
                            'user_is_any_organization_member': any_org_member,
                            'single_org_membership': single_org_membership,
                            'organization_memberships': organization_memberships,
                        })

def add_project_common_context(request, project, page_tab, context):
    context['project'] = project
    context['page_tab'] = page_tab
    if not request.user.is_anonymous:
        context['user_is_following_project'] = ProjectService.user_is_project_follower(request.user, project)
    return context

def add_project_task_common_context(request, project_task, page_tab, context):
    # We get the project from the domain layer so it comes back properly annotated
    add_project_common_context(request, get_project(request, project_task.project.id), page_tab, context)
    context['project_task'] = project_task
    context['project_tasks'] = ProjectTaskService.get_project_tasks_summary(request.user, project_task.project)
    return context

class ProjectView(PermissionRequiredMixin, generic.ListView): ## This is a listview because it is actually showing the list of open tasks
    model = ProjectTask
    template_name = 'dssgmkt/proj_info.html'
    context_object_name = 'project_tasks'
    paginate_by = 25
    permission_required = 'project.view'
    raise_exception = True
    allow_empty = True

    def get_queryset(self):
        return ProjectTaskService.get_public_tasks(self.request.user, self.kwargs['proj_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project)
        context['volunteers'] = ProjectService.get_project_public_volunteer_list(self.request.user, self.kwargs['proj_pk'])
        add_project_common_context(self.request, project, 'info', context)
        return context

    def get_permission_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])

class ProjectLogView(PermissionRequiredMixin, generic.ListView):
    template_name = 'dssgmkt/proj_log.html'
    context_object_name = 'project_logs'
    paginate_by = 20
    permission_required = 'project.log_view'
    raise_exception = True
    allow_empty = True

    def get_queryset(self):
        project = get_project(self.request, self.kwargs['proj_pk'])
        return ProjectService.get_project_changes(self.request.user, project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project, ('Change log', None))
        add_project_common_context(self.request, project, 'log', context)
        return context

    def get_permission_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])

class CreateProjectCommentForm(ModelForm):
    class Meta:
        model = ProjectComment
        fields = ['comment']


def project_comment_channel_index_view(request, proj_pk):
    if request.method == 'POST':
        raise Http404
    elif request.method == 'GET':
        project = get_project(request, proj_pk)
        discussion_channels = ProjectService.get_project_channels(request.user, project)
        return render(request, 'dssgmkt/proj_discussion_channels.html',
                        add_project_common_context(
                            request,
                            project,
                            'discussion',
                            {
                                'breadcrumb': project_breadcrumb(project, discussion_index_link(project, include_link=False)),
                                'discussion_channels': discussion_channels
                            }))

def project_channel_comments_view(request, proj_pk, channel_pk):
    if request.method == 'POST':
        form = CreateProjectCommentForm(request.POST)
        if form.is_valid():
            project_comment = form.save(commit = False)
            try:
                ProjectService.add_project_comment(request.user, proj_pk, channel_pk, project_comment)
                messages.info(request, 'Comment added successfuly')
                return redirect('dssgmkt:proj_discussion', proj_pk=proj_pk, channel_pk=channel_pk)
            except KeyError:
                raise Http404
            except ValueError:
                form.add_error(None, "Invalid comment.")
    elif request.method == 'GET':
        form = CreateProjectCommentForm()
    project = get_project(request, proj_pk)
    project_comments = ProjectService.get_project_comments(request.user, channel_pk, project)
    project_comments_page = paginate(request, project_comments, page_size=20)
    channel = ProjectService.get_project_channel(request.user, project, channel_pk)
    discussion_channels = ProjectService.get_project_channels(request.user, project)
    return render(request, 'dssgmkt/proj_discussion.html',
                    add_project_common_context(
                        request,
                        project,
                        'discussion',
                        {
                            'breadcrumb': project_breadcrumb(project, discussion_index_link(project), (channel.name, None)),
                            'project_comments': project_comments_page,
                            'form': form,
                            'channel': channel_pk,
                            'discussion_channels': discussion_channels
                        }))

class ProjectDeliverablesView(generic.DetailView):
    model = Project
    template_name = 'dssgmkt/proj_deliverables.html'
    pk_url_kwarg = 'proj_pk'

    def get_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = project_breadcrumb(context['project'], ('Project deliverables', None))
        project = get_project(self.request, self.kwargs['proj_pk'])
        add_project_common_context(self.request, project, 'deliverables', context)
        return context


@permission_required('project.scope_view', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def project_scope_view(request, proj_pk, scope_pk=None):
    if request.method == 'GET':
        project = get_project(request, proj_pk)
        project_scopes = ProjectService.get_all_project_scopes(request.user, proj_pk)
        scopes_page = paginate(request, project_scopes, page_size=10)
        if scope_pk:
            current_scope = get_project_scope(request, proj_pk, scope_pk)
            showing_current_scope = current_scope == ProjectService.get_current_project_scope(request.user, proj_pk)
        else:
            current_scope = ProjectService.get_current_project_scope(request.user, proj_pk)
            showing_current_scope = True
        return render(request, 'dssgmkt/proj_scope.html',
                        add_project_common_context(request, project, 'scope',
                            {
                                'breadcrumb': project_breadcrumb(project, ('Scope', None)),
                                'current_scope': current_scope,
                                'project_scopes': scopes_page,
                                'showing_current_scope': showing_current_scope
                            }))
    else:
        raise Http404


class EditProjectScopeForm(ModelForm):
    class Meta:
        model = ProjectScope
        fields = ['version_notes', 'scope', 'project_impact', 'scoping_process', 'available_staff', 'available_data']

@permission_required('project.scope_edit', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def project_edit_scope_view(request, proj_pk, scope_pk):
    project = get_project(request, proj_pk)
    project_scope = get_project_scope(request, proj_pk, scope_pk)
    project_scope.version_notes = None
    if request.method == 'POST':
        form = EditProjectScopeForm(request.POST, instance=project_scope)
        if form.is_valid():
            project_scope = form.save(commit = False)
            try:
                ProjectService.update_project_scope(request.user, proj_pk, project_scope)
                messages.info(request, 'Project scope edited successfully.')
                return redirect('dssgmkt:proj_scope', proj_pk=proj_pk)
            except ValueError as v:
                form.add_error(None, str(v))
            except KeyError:
                raise Http404
    elif request.method == 'GET':
        form = EditProjectScopeForm(instance=project_scope)
    return render(request, 'dssgmkt/proj_scope_edit.html',
                    add_project_common_context(request, project, 'scope',
                        {
                            'breadcrumb': project_breadcrumb(project, ('Scope', reverse('dssgmkt:proj_scope',  args=[proj_pk])), ('Edit', None)),
                            'project_scope': project_scope,
                            'form': form
                        }))

class ProjectVolunteerInstructionsView(PermissionRequiredMixin, generic.ListView):
    template_name = 'dssgmkt/proj_instructions.html'
    context_object_name = 'project_tasks'
    permission_required = 'project.volunteer_instructions_view'
    raise_exception = True
    allow_empty = True

    def get_queryset(self):
        return ProjectTaskService.get_volunteer_current_tasks(self.request.user, self.request.user, self.kwargs['proj_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project, ('Volunteer instructions', None))
        context['project_tasks'] = ProjectTaskService.get_volunteer_all_project_tasks(self.request.user, self.request.user, project)
        # context['task_volunteers'] = ProjectTaskService.get_task_volunteers(self.request.user, self.kwargs['task_pk'])
        add_project_common_context(self.request, project, 'instructions', context)
        return context

    def get_permission_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])


class ProjectVolunteerTaskDetailView(generic.DetailView):
    model = ProjectTask
    template_name = 'dssgmkt/proj_instructions_task.html'
    pk_url_kwarg = 'task_pk'

    def get_object(self):
        return get_project_task(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task = get_project_task(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])
        context['breadcrumb'] = project_volunteer_task_breadcrumb(project_task)
        context['task_volunteers'] = ProjectTaskService.get_task_volunteers(self.request.user, self.kwargs['task_pk'])
        add_project_task_common_context(self.request, project_task, 'instructions', context)
        context['project_tasks'] = ProjectTaskService.get_volunteer_all_project_tasks(self.request.user, self.request.user, project_task.project) # override the default tasks in the project.
        return context



class CreateProjectTaskReviewForm(ModelForm):
    class Meta:
        model = ProjectTaskReview
        fields = ['volunteer_comment', 'volunteer_effort_hours']

class ProjectTaskReviewCreate(PermissionRequiredMixin, CreateView):
    model = ProjectTaskReview
    fields = ['volunteer_comment', 'volunteer_effort_hours']
    template_name = 'dssgmkt/proj_task_finish.html'
    permission_required = 'project.volunteer_task_finish'
    raise_exception = True

    def get_success_url(self):
        return reverse('dssgmkt:proj_instructions_task', args=[self.kwargs['proj_pk'], self.kwargs['task_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task = get_project_task(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])
        context['breadcrumb'] = project_volunteer_task_breadcrumb(project_task,
                                                                    ('Mark work as completed', None))
        add_project_task_common_context(self.request, project_task, 'instructions', context)
        context['project_tasks'] = ProjectTaskService.get_volunteer_all_project_tasks(self.request.user, self.request.user, project_task.project) # override the default tasks in the project.
        return context

    def form_valid(self, form):
        project_task_review = form.save(commit=False)
        try:
            ProjectTaskService.mark_task_as_completed(self.request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], project_task_review)
            messages.info(self.request, "Task marked as completed, waiting for QA review.")
            return HttpResponseRedirect(self.get_success_url())
        except KeyError:
            raise Http404

    def get_permission_object(self):
        return get_project_task(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])

class ProjectTaskReviewForm(ModelForm):
    class Meta:
        model = ProjectTaskReview
        fields = ['review_score', 'public_reviewer_comments', 'private_reviewer_notes']


@permission_required('project.task_review_view', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def process_task_review_request_view(request, proj_pk, task_pk, review_pk, action=None):
    project_task_review = get_project_task_review(request, proj_pk, task_pk, review_pk)
    if request.method == 'POST':
        form = ProjectTaskReviewForm(request.POST, instance=project_task_review)
        if form.is_valid():
            project_task_review = form.save(commit = False)
            try:
                if action == 'accept':
                    ProjectTaskService.accept_task_review(request.user, proj_pk, task_pk, project_task_review)
                    messages.info(request, 'Task accepted as completed.')
                else:
                    ProjectTaskService.reject_task_review(request.user, proj_pk, task_pk, project_task_review)
                    messages.warning(request, 'Task rejected as completed and reopened.')
                return redirect('dssgmkt:proj_task', proj_pk=proj_pk, task_pk=task_pk)
            except KeyError:
                raise Http404
    elif request.method == 'GET':
        form = ProjectTaskReviewForm()
    project_task = get_project_task(request, proj_pk, task_pk)
    project = project_task.project

    return render(request, 'dssgmkt/proj_task_review.html',
                    add_project_task_common_context(
                        request,
                        project_task,
                        'tasklist',
                        {
                            'task_review': project_task_review,
                            'breadcrumb': project_breadcrumb(project,
                                                                tasks_link(project),
                                                                task_link(project_task),
                                                                ('Review completed task', None)),
                            'form': form,
                        }))


class ProjectTaskCancel(PermissionRequiredMixin, DeleteView):
    model = ProjectTaskRole
    template_name = 'dssgmkt/proj_task_cancel.html'
    permission_required = 'project.volunteer_task_cancel'
    raise_exception = True

    def get_object(self):
        return get_own_project_task_role(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])

    def get_success_url(self):
        return reverse('dssgmkt:proj_instructions', args=[self.object.task.project.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task_role = self.object
        project_task = project_task_role.task
        project = project_task.project
        context['breadcrumb'] = project_volunteer_task_breadcrumb(project_task,
                                                                    ('Stop volunteering', None))
        add_project_task_common_context(self.request, project_task, 'instructions', context)
        context['project_tasks'] = ProjectTaskService.get_volunteer_all_project_tasks(self.request.user, self.request.user, project) # override the default tasks in the project.
        return context

    def delete(self, request,  *args, **kwargs):
        project_task_role = self.get_object()
        self.object = project_task_role
        try:
            ProjectTaskService.cancel_volunteering(request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], project_task_role)
            messages.info(request, 'You stopped working on ' + project_task_role.task.name + ' successfully.')
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as err:
            messages.error(request, 'There was a problem with your request.')
            # logger.error("Error when user {0} tried to leave organization {1}: {2}".format(request.user.id, organization_role.organization.id, err))
            return HttpResponseRedirect(self.get_success_url())
        return context

    def get_permission_object(self):
        return get_project_task(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])


class ProjectTaskApply(PermissionRequiredMixin, CreateView):
    model = VolunteerApplication
    fields = ['volunteer_application_letter']
    template_name = 'dssgmkt/proj_task_apply.html'
    permission_required = 'user.is_authenticated'
    raise_exception = True

    def get_success_url(self):
        return reverse('dssgmkt:proj_info', args=[self.kwargs['proj_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task = get_project_task(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project, ('Apply to volunteer', None))
        add_project_task_common_context(self.request, project_task, 'info', context)
        return context

    def form_valid(self, form):
        task_application_request = form.save(commit=False)
        try:
            ProjectTaskService.apply_to_volunteer(self.request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], task_application_request)
            messages.info(self.request, 'You have applied to work on ' + task_application_request.task.name + '. The project staff will evaluate your request and notify you of the results of the review.')
            return HttpResponseRedirect(self.get_success_url())
        except KeyError:
            raise Http404
        except ValueError as v:
            form.add_error(None, str(v))
            return self.form_invalid(form)


class ProjectTaskIndex(PermissionRequiredMixin, generic.ListView):
    model = ProjectTask
    template_name = 'dssgmkt/proj_task_list.html'
    context_object_name = 'project_tasks'
    permission_required = 'project.tasks_view'
    raise_exception = True
    allow_empty = True

    def get_queryset(self):
        project = get_project(self.request, self.kwargs['proj_pk'])
        return ProjectTaskService.get_project_tasks_summary(self.request.user, project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project, tasks_link(project, include_link=False))
        add_project_common_context(self.request, project, 'tasklist', context)
        return context

    def get_permission_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])



class ProjectTaskDetailView(generic.DetailView):
    model = ProjectTask
    template_name = 'dssgmkt/proj_task.html'
    pk_url_kwarg = 'task_pk'

    def get_object(self):
        return get_project_task(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task = get_project_task(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])
        context['breadcrumb'] = project_task_breadcrumb(project_task)
        context['task_volunteers'] = ProjectTaskService.get_task_volunteers(self.request.user, self.kwargs['task_pk'])
        add_project_task_common_context(self.request, project_task, 'tasklist', context)
        return context



class ProjectTaskEdit(PermissionRequiredMixin, UpdateView):
    model = ProjectTask
    fields = ['name', 'description', 'type', 'onboarding_instructions', 'stage', 'accepting_volunteers', 'estimated_start_date',
                'estimated_end_date', 'estimated_effort_hours', 'task_home_url', 'task_deliverables_url']
    template_name = 'dssgmkt/proj_task_edit.html'
    pk_url_kwarg = 'task_pk'
    permission_required = 'project.task_edit'
    raise_exception = True

    def get_success_url(self):
        return reverse('dssgmkt:proj_task', args=[self.kwargs['proj_pk'], self.kwargs['task_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        project_task = self.object
        context['breadcrumb'] = project_breadcrumb(project,
                                                    tasks_link(project),
                                                    task_link(project_task),
                                                    ('Edit project task', None))
        add_project_task_common_context(self.request, project_task, 'tasklist', context)
        return context

    def form_valid(self, form):
        project_task = form.save(commit = False)
        try:
            ProjectTaskService.save_task(self.request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], project_task)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as v:
            return super().form_invalid(form)

    def get_permission_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])

class ProjectEdit(PermissionRequiredMixin, UpdateView):
    model = Project
    fields = ['name', 'short_summary', 'motivation','solution_description', 'challenges', 'banner_image_url', 'project_cause',
            'developer_agreement', 'intended_start_date',
            'intended_end_date', 'deliverables_description', 'deliverable_github_url', 'deliverable_management_url', 'deliverable_documentation_url',
            'deliverable_reports_url', 'status']
    template_name = 'dssgmkt/proj_info_edit.html'
    pk_url_kwarg = 'proj_pk'
    permission_required = 'project.information_edit'
    raise_exception = True

    def get_success_url(self):
        return reverse('dssgmkt:proj_info', args=[self.kwargs['proj_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project, ('Edit project information', None))
        add_project_common_context(self.request, project, 'info', context)
        return context

    def form_valid(self, form):
        project = form.save(commit = False)
        try:
            ProjectService.save_project(self.request.user, self.kwargs['proj_pk'], project)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as v:
            form.add_error(None, str(v))
            return super().form_invalid(form)



@permission_required('project.task_requirements_view', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def project_task_requirements_edit_view(request, proj_pk, task_pk):
    task = get_project_task(request, proj_pk, task_pk)
    project = get_project(request, proj_pk)
    if request.method == 'POST':
        try:
            ProjectTaskService.set_task_requirements(request.user, proj_pk, task_pk, request.POST)
            return redirect('dssgmkt:proj_task', proj_pk=proj_pk, task_pk=task_pk)
        except KeyError:
            raise Http404
        except ValueError:
            pass
    elif request.method == 'GET':
        pass
    return render(request, 'dssgmkt/proj_task_requirements_edit.html',
                    add_project_task_common_context(request, task, 'tasklist',
                        {
                            'breadcrumb': project_breadcrumb(project,
                                                            tasks_link(project),
                                                            task_link(task),
                                                            edit_task_requirements_link(project, task, include_link=False)),
                            'system_skills': get_project_task_requirements(request, proj_pk, task_pk),
                            'skill_levels': UserService.get_skill_levels(),
                            'importance_levels': ProjectTaskService.get_project_taks_requirement_importance_levels(),
                        }))

class ProjectTaskRemove(PermissionRequiredMixin, DeleteView):
    model = ProjectTask
    template_name = 'dssgmkt/proj_task_remove.html'
    pk_url_kwarg = 'task_pk'
    permission_required = 'project.task_delete'
    raise_exception = True

    def get_success_url(self):
        return reverse('dssgmkt:proj_task_list', args=[self.kwargs['proj_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task = self.object
        if project_task:
            project = project_task.project
            context['breadcrumb'] =  project_breadcrumb(project,
                                                            tasks_link(project),
                                                            task_link(project_task),
                                                            ('Delete task', None))
            add_project_task_common_context(self.request, project_task, 'tasklist', context)
            return context
        else:
            raise Http404

    def delete(self, request,  *args, **kwargs):
        project_task = self.get_object()
        self.object = project_task
        try:
            ProjectTaskService.delete_task(request.user, self.kwargs['proj_pk'], project_task)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as err:
            messages.error(request, 'There was a problem with your request.')
            # logger.error("Error when user {0} tried to leave organization {1}: {2}".format(request.user.id, organization_role.organization.id, err))
            return HttpResponseRedirect(self.get_success_url())

    def get_permission_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])


def create_default_project_task(request, proj_pk):
    if request.method == 'GET':
        raise Http404
    elif request.method == 'POST':
        new_task = ProjectTaskService.create_default_task(request.user, proj_pk)
        return redirect('dssgmkt:proj_task_edit', proj_pk=proj_pk, task_pk=new_task.id)


class CreateProjectRoleForm(ModelForm):
    class Meta:
        model = ProjectRole
        fields = ['role', 'user']

@permission_required('project.staff_view', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def project_staff_view(request, proj_pk):
    if request.method == 'POST':
        form = CreateProjectRoleForm(request.POST)
        if form.is_valid:
            project_role = form.save(commit = False)
            try:
                ProjectService.add_staff_member(request.user, proj_pk, project_role)
                messages.info(request, 'Staff member added successfully.')
                return redirect('dssgmkt:proj_staff', proj_pk=proj_pk)
            except KeyError:
                raise Http404
            except ValueError:
                form.add_error(None, "This user is already a member of the project.")
    elif request.method == 'GET':
        form = CreateProjectRoleForm()
    project = get_project(request, proj_pk)
    project_staff = ProjectService.get_all_project_staff(request.user, proj_pk)
    staff_page = paginate(request, project_staff, request_key='staff_page', page_size=20)

    return render(request, 'dssgmkt/proj_staff.html',
                    add_project_common_context(request, project, 'staff',
                        {
                            'breadcrumb': project_breadcrumb(project, ('Staff', None)),
                            'project_staff': staff_page,
                            'add_staff_form': form,
                        }))


@permission_required('project.volunteers_view', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def project_volunteers_view(request, proj_pk):
    if request.method == 'GET':
        project = get_project(request, proj_pk)
        volunteers = ProjectService.get_all_project_volunteers(request.user, proj_pk)
        volunteers_page = paginate(request, volunteers, request_key='volunteers_page', page_size=20)

        volunteer_applications = ProjectService.get_all_volunteer_applications(request.user, proj_pk)
        applications_page = paginate(request, volunteer_applications, request_key='applications_page', page_size=20)

        return render(request, 'dssgmkt/proj_volunteers.html',
                        add_project_common_context(request, project, 'volunteers',
                            {
                                'breadcrumb': project_breadcrumb(project, ('Volunteers', None)),
                                'volunteers': volunteers_page,
                                'volunteer_applications': applications_page,
                            }))


class ProjectRoleEdit(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProjectRole
    fields = ['role']
    template_name = 'dssgmkt/proj_staff_edit.html'
    pk_url_kwarg = 'role_pk'
    success_message = 'Role edited successfully'
    permission_required = 'project.staff_edit'
    raise_exception = True

    def get_success_url(self):
        return reverse('dssgmkt:proj_staff', args=[self.object.project.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_role = self.object
        if project_role and project_role.project.id == self.kwargs['proj_pk']:
            project = self.object.project
            context['breadcrumb'] =  project_breadcrumb(project,
                                                        staff_link(project),
                                                        ('Edit staff member', None))
            add_project_common_context(self.request, project, 'staff', context)
            return context
        else:
            raise Http404

    def form_valid(self, form):
        project_role = form.save(commit = False)
        try:
            ProjectService.save_project_role(self.request.user, self.kwargs['proj_pk'], project_role)
            return HttpResponseRedirect(self.get_success_url())
        except KeyError as k:
            form.add_error(None, str(k))
            return super().form_invalid(form)
        except ValueError as v:
            form.add_error(None, str(v))
            return super().form_invalid(form)

    def get_permission_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])

class DeleteProjectRoleForm(ModelForm):
    class Meta:
        model = ProjectRole
        fields = []

@permission_required('project.staff_remove', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def project_role_delete_view(request, proj_pk, role_pk):
    project_role = get_project_role(request, proj_pk, role_pk)
    if request.method == 'POST':
        form = DeleteProjectRoleForm(request.POST)
        if form.is_valid():
            try:
                ProjectService.delete_project_role(request.user, proj_pk, project_role)
                messages.info(request, 'Staff member removed successfully.')
                return redirect('dssgmkt:proj_staff', proj_pk=proj_pk)
            except KeyError:
                raise Http404
            except ValueError as err:
                form.add_error(None, str(err))
    elif request.method == 'GET':
        form = DeleteProjectRoleForm()
    project = get_project(request, proj_pk)
    return render(request, 'dssgmkt/proj_staff_remove.html',
                    add_project_common_context(request, project, 'staff',
                        {
                            'projectrole': project_role,
                            'breadcrumb': project_breadcrumb(project,
                                                                staff_link(project),
                                                                ('Remove staff member', None)),
                            'form': form,
                        }))


class EditProjectTaskRoleForm(ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(EditProjectTaskRoleForm, self).__init__(*args, **kwargs)
        self.fields['task'].queryset = ProjectTaskService.get_non_finished_tasks(user, self.instance.task.project)

    class Meta:
        model = ProjectTaskRole
        fields = ['task']

class ProjectTaskRoleEdit(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProjectTaskRole
    form_class = EditProjectTaskRoleForm
    template_name = 'dssgmkt/proj_task_volunteer_edit.html'
    pk_url_kwarg = 'task_role_pk'
    success_message = 'Volunteer edited successfully'
    permission_required = 'project.volunteers_edit'
    raise_exception = True

    def get_form_kwargs(self):
        kwargs = super(ProjectTaskRoleEdit, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('dssgmkt:proj_volunteers', args=[self.object.task.project.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task_role = self.object
        if project_task_role and project_task_role.task.id == self.kwargs['task_pk'] and project_task_role.task.project.id == self.kwargs['proj_pk']:
            project_task = project_task_role.task
            project = project_task.project
            context['breadcrumb'] =  project_breadcrumb(project,
                                                        volunteers_link(project),
                                                        ('Change volunteer task', None))
            add_project_task_common_context(self.request, project_task, 'volunteers', context)
            return context
        else:
            raise Http404

    def form_valid(self, form):
        project_task_role = form.save(commit = False)
        try:
            ProjectTaskService.save_project_task_role(self.request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], project_task_role)
            return HttpResponseRedirect(self.get_success_url())
        except KeyError:
            return super().form_invalid(form)

    def get_permission_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])

class ProjectTaskRoleRemove(PermissionRequiredMixin, DeleteView):
    model = ProjectTaskRole
    template_name = 'dssgmkt/proj_volunteer_remove.html'
    permission_required = 'project.volunteers_remove'
    raise_exception = True

    def get_object(self):
        return get_project_task_role(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'], self.kwargs['task_role_pk'])

    def get_success_url(self):
        return reverse('dssgmkt:proj_volunteers', args=[self.object.task.project.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task_role = self.object
        project_task = project_task_role.task
        project = project_task.project
        context['breadcrumb'] = project_breadcrumb(project,
                                                    volunteers_link(project),
                                                    ('Remove volunteer', None))
        add_project_task_common_context(self.request, project_task, 'volunteers', context)
        return context

    def delete(self, request,  *args, **kwargs):
        project_task_role = self.get_object()
        self.object = project_task_role
        try:
            ProjectTaskService.delete_project_task_role(request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], project_task_role)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as err:
            messages.error(request, 'There was a problem with your request.')
            # logger.error("Error when user {0} tried to leave organization {1}: {2}".format(request.user.id, organization_role.organization.id, err))
            return HttpResponseRedirect(self.get_success_url())

    def get_permission_object(self):
        return get_project(self.request, self.kwargs['proj_pk'])

class VolunteerApplicationReviewForm(ModelForm):

    class Meta:
        model = VolunteerApplication
        fields = ['public_reviewer_comments', 'private_reviewer_notes']

@permission_required('project.volunteers_application_view', raise_exception=True, fn=objectgetter(VolunteerApplication, 'volunteer_application_pk'))
def volunteer_application_view(request, proj_pk, task_pk, volunteer_application_pk, action=None):
    volunteer_application = get_volunteer_application(request, proj_pk, task_pk, volunteer_application_pk)
    if request.method == 'POST':
        form = VolunteerApplicationReviewForm(request.POST, instance=volunteer_application)
        if form.is_valid():
            volunteer_application = form.save(commit = False)
            try:
                if action == 'accept':
                    ProjectTaskService.accept_volunteer(request.user, proj_pk, task_pk, volunteer_application)
                    messages.info(request, 'Volunteer application accepted.')
                else:
                    ProjectTaskService.reject_volunteer(request.user, proj_pk, task_pk, volunteer_application)
                    messages.info(request, 'Volunteer application rejected.')
                return redirect('dssgmkt:proj_volunteers', proj_pk=proj_pk)
            except KeyError:
                raise Http404
    elif request.method == 'GET':
        form = VolunteerApplicationReviewForm()

    project = get_project(request, proj_pk)
    if volunteer_application and volunteer_application.task.id == task_pk and volunteer_application.task.project.id == proj_pk:
        return render(request, 'dssgmkt/proj_volunteer_application_review.html',
                        add_project_common_context(
                            request,
                            project,
                            'volunteers',
                            {
                                'volunteerapplication': volunteer_application,
                                'breadcrumb': project_breadcrumb(project,
                                                                    volunteers_link(project),
                                                                    ('Review volunteer', None)),
                                'user_is_applicant': volunteer_application.volunteer == request.user,
                                'form': form,
                            }))
    else:
        raise Http404


def follow_project_view(request, proj_pk):
    if request.method == 'GET':
        raise Http404
    elif request.method == 'POST':
        try:
            ProjectService.toggle_follower(request.user, proj_pk)
            return redirect('dssgmkt:proj_info', proj_pk=proj_pk)
        except KeyError:
            messages.error(request, 'There was an error while processing your request.')
            return redirect('dssgmkt:proj_info', proj_pk=proj_pk)


@permission_required('project.publish', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def publish_project_view(request, proj_pk):
    project = get_project(request, proj_pk)
    if request.method == 'POST':
        try:
            ProjectService.publish_project(request.user, proj_pk, project)
            return redirect('dssgmkt:proj_info', proj_pk=proj_pk)
        except KeyError:
            messages.error(request, 'There was an error while processing your request.')
            return redirect('dssgmkt:proj_info', proj_pk=proj_pk)
    elif request.method == 'GET':
        pass
    if project:
        return render(request, 'dssgmkt/proj_publish.html',
                        add_project_common_context(
                            request,
                            project,
                            'info',
                            {
                                'breadcrumb': project_breadcrumb(project,
                                                                    ('Publish project', None)),
                            }))
    else:
        raise Http404


@permission_required('project.approve_as_completed', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def finish_project_view(request, proj_pk):
    project = get_project(request, proj_pk)
    if request.method == 'POST':
        try:
            ProjectService.finish_project(request.user, proj_pk, project)
            return redirect('dssgmkt:proj_info', proj_pk=proj_pk)
        except KeyError:
            messages.error(request, 'There was an error while processing your request.')
            return redirect('dssgmkt:proj_info', proj_pk=proj_pk)
    elif request.method == 'GET':
        pass
    if project:
        return render(request, 'dssgmkt/proj_finish.html',
                        add_project_common_context(
                            request,
                            project,
                            'info',
                            {
                                'breadcrumb': project_breadcrumb(project,
                                                                    ('Finish project', None)),
                            }))
    else:
        raise Http404

@permission_required('project.task_edit', raise_exception=True, fn=objectgetter(Project, 'proj_pk'))
def toggle_task_accepting_volunteers_view(request, proj_pk, task_pk):
    if request.method == 'GET':
        raise Http404
    elif request.method == 'POST':
        try:
            ProjectTaskService.toggle_task_accepting_volunteers(request.user, proj_pk, task_pk)
            return redirect('dssgmkt:proj_task', proj_pk=proj_pk, task_pk=task_pk)
        except KeyError:
            messages.error(request, 'There was an error while processing your request.')
            return redirect('dssgmkt:proj_task', proj_pk=proj_pk, task_pk=task_pk)



class CreateProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'project_cause', 'short_summary', 'motivation',
                    'solution_description', 'challenges', 'banner_image_url',
                    'developer_agreement', 'project_impact', 'scoping_process',
                    'available_staff', 'available_data', 'intended_start_date',
                    'intended_end_date', 'deliverable_github_url',
                    'deliverable_management_url', 'deliverable_documentation_url',
                    'deliverable_reports_url',]

class ProjectCreateView(PermissionRequiredMixin, CreateView):
    model = Project
    form_class = CreateProjectForm
    template_name = 'dssgmkt/proj_create.html'
    permission_required = 'organization.project_create'
    raise_exception = True

    def get_success_url(self):
        return reverse('dssgmkt:proj_info', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = get_organization(self.request, self.kwargs['org_pk'])
        context['breadcrumb'] = [home_link(), organizations_link(), organization_link(organization), ('Create new project', None)]
        return add_organization_common_context(
            self.request,
            organization,
            'info',
            context)

    def form_valid(self, form):
        project = form.save(commit=False)
        try:
            project = OrganizationService.create_project(self.request.user, self.kwargs['org_pk'], project)
            messages.info(self.request, "The project was created successfully and you were assigned administrator privileges over it.")
            self.object = project
            return HttpResponseRedirect(self.get_success_url())
        except KeyError:
            raise Http404
        except ValueError as v:
            form.add_error(None, str(v))
            return self.form_invalid(form)

    def get_permission_object(self):
        return get_organization(self.request, self.kwargs['org_pk'])

def project_create_select_organization_view(request):
    return render(request, 'dssgmkt/proj_create_org_select.html',
                        {
                            'breadcrumb': [home_link(), ('Select organization', None)],
                            'user_organizations': OrganizationService.get_organizations_with_user_create_project_permission(request.user),
                        })
