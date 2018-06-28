from datetime import date

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
    ProjectTaskReview, ProjectTaskRole, VolunteerApplication,
)
from .common import build_breadcrumb, home_link, paginate
from dssgmkt.domain.proj import ProjectService, ProjectTaskService

def projects_link(include_link=True):
    return ('Projects', reverse('dssgmkt:proj_list') if include_link else None)

def project_link(project, include_link=True):
    return (project.name, reverse('dssgmkt:proj_info', args=[project.id]) if include_link else None)

def staff_link(project, include_link=True):
    return ('Staff', reverse('dssgmkt:proj_staff', args=[project.id]) if include_link else None)

def volunteers_link(project, include_link=True):
    return ('Volunteers', reverse('dssgmkt:proj_volunteers', args=[project.id]) if include_link else None)

def volunteer_instructions_link(project, include_link=True):
    return ('Volunteer instructions', reverse('dssgmkt:proj_instructions', args=[project.id]) if include_link else None)

def tasks_link(project, include_link=True):
    return ('Tasks', reverse('dssgmkt:proj_task_list', args=[project.id]) if include_link else None)

def edit_task_requirements_link(project, task, include_link=True):
    return ('Edit project task requirements', reverse('dssgmkt:proj_task_requirements_edit', args=[project.id, task.id]) if include_link else None)

def project_breadcrumb(project, *items):
    breadcrumb_items = [home_link(),
                        projects_link(),
                        project_link(project, items)]
    breadcrumb_items += items
    return build_breadcrumb(breadcrumb_items)

def get_project(request, proj_pk):
    project = ProjectService.get_project(request.user, proj_pk)
    if project:
        return project
    else:
        raise Http404

def get_project_task(request, proj_pk, task_pk):
    project_task = ProjectTaskService.get_project_task(request.user, proj_pk, task_pk)
    if project_task:
        return project_task
    else:
        raise Http404

def get_project_task_role(request, proj_pk, task_pk, role_pk):
    project_task_role = ProjectTaskService.get_project_task_role(request.user, proj_pk, task_pk, role_pk)
    if project_task_role:
        return project_task_role
    else:
        raise Http404

def get_own_project_task_role(request, proj_pk, task_pk):
    project_task_role = ProjectTaskService.get_own_project_task_role(request.user, proj_pk, task_pk)
    if project_task_role:
        return project_task_role
    else:
        raise Http404

def get_project_task_review(request, proj_pk, task_pk, review_pk):
    project_task_review = ProjectTaskService.get_project_task_review(request.user, proj_pk, task_pk, review_pk)
    if project_task_review:
        return project_task_review
    else:
        raise Http404

def get_project_task_requirements(request, proj_pk, task_pk):
    project_task_requirements = ProjectTaskService.get_project_task_requirements(request.user, proj_pk, task_pk)
    if project_task_requirements:
        return project_task_requirements
    else:
        raise Http404

def get_volunteer_application(request, proj_pk, task_pk, volunteer_application_pk):
    volunteer_application = ProjectTaskService.get_volunteer_application(request.user, proj_pk, task_pk, volunteer_application_pk)
    if volunteer_application:
        return volunteer_application
    else:
        raise Http404

class ProjectIndexView(generic.ListView):
    template_name = 'dssgmkt/proj_list.html'
    context_object_name = 'proj_list'
    paginate_by = 1

    def get_queryset(self):
        # This gets paginated by the view so we are not retrieving all the projects in one query
        return ProjectService.get_all_projects(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = build_breadcrumb([home_link(),
                                                  projects_link(False)])
        return context


def add_project_common_context(request, project, page_tab, context):
    context['project'] = project
    context['page_tab'] = page_tab
    if not request.user.is_anonymous:
        context['user_is_following_project'] = ProjectService.user_is_project_follower(request.user, project)
        context['user_is_project_member'] = ProjectService.user_is_project_member(request.user, project)
        context['user_is_project_owner'] = ProjectService.user_is_project_owner(request.user, project)
    return context

def add_project_task_common_context(request, project_task, page_tab, context):
    add_project_common_context(request, project_task.project, page_tab, context)
    context['project_task'] = project_task
    return context

class ProjectView(generic.ListView): ## This is a listview because it is actually showing the list of open tasks
    model = ProjectTask
    template_name = 'dssgmkt/proj_info.html'
    context_object_name = 'project_tasks'
    paginate_by = 50

    def get_queryset(self):
        return ProjectTaskService.get_open_tasks(self.request.user, self.kwargs['proj_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project)
        add_project_common_context(self.request, project, 'info', context)
        return context

class ProjectLogView(generic.ListView):
    template_name = 'dssgmkt/proj_log.html'
    context_object_name = 'project_logs'
    paginate_by = 1

    def get_queryset(self):
        project = get_project(self.request, self.kwargs['proj_pk'])
        return ProjectService.get_project_changes(self.request.user, project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project, ('Change log', None))
        add_project_common_context(self.request, project, 'log', context)
        return context

class CreateProjectCommentForm(ModelForm):
    class Meta:
        model = ProjectComment
        fields = ['comment']


def project_comments_view(request, proj_pk):
    ## TODO this is a security hole as anybody can post to this view and create new skills
    if request.method == 'POST':
        form = CreateProjectCommentForm(request.POST)
        if form.is_valid():
            project_comment = form.save(commit = False)
            try:
                ProjectService.add_project_comment(request.user, proj_pk, project_comment)
                messages.info(request, 'Comment added successfuly')
                return redirect('dssgmkt:proj_discussion', proj_pk = proj_pk)
            except KeyError:
                raise Http404
            except ValueError:
                form.add_error(None, "Invalid comment.")
    elif request.method == 'GET':
        form = CreateProjectCommentForm()
    project = get_project(request, proj_pk)
    project_comments = ProjectService.get_project_comments(request.user, project)
    project_comments_page = paginate(request, project_comments, page_size=20)
    return render(request, 'dssgmkt/proj_discussion.html',
                    add_project_common_context(
                        request,
                        project,
                        'discussion',
                        {
                            'breadcrumb': project_breadcrumb(project, ('Discussion', None)),
                            'project_comments': project_comments_page,
                            'form': form,
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

class ProjectVolunteerInstructionsView(generic.ListView):
    template_name = 'dssgmkt/proj_instructions.html'
    context_object_name = 'project_tasks'

    def get_queryset(self):
        return ProjectTaskService.get_volunteer_current_tasks(self.request.user, self.request.user, self.kwargs['proj_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project, ('Volunteer instructions', None))
        add_project_common_context(self.request, project, 'instructions', context)
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
        project_task = get_project_task(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])
        context['breadcrumb'] = project_breadcrumb(project_task.project,
                                                    volunteer_instructions_link(project_task.project),
                                                    ('Mark work as completed', None))
        add_project_task_common_context(self.request, project_task, 'instructions', context)
        return context

    def form_valid(self, form):
        project_task_review = form.save(commit=False)
        try:
            ProjectTaskService.mark_task_as_completed(self.request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], project_task_review)
            return HttpResponseRedirect(self.get_success_url())
        except KeyError:
            raise Http404

class ProjectTaskReviewView(generic.DetailView):
    model = ProjectTaskReview
    template_name = 'dssgmkt/proj_task_review_detail.html'
    pk_url_kwarg = 'review_pk'

    def get_object(self):
        return get_project_task_review(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'], self.kwargs['review_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_review = self.object
        project_task = task_review.task
        project = project_task.project
        context['breadcrumb'] = project_breadcrumb(project,
                                                    tasks_link(project),
                                                    ('Task review request', None))
        add_project_task_common_context(self.request, project_task, 'tasklist', context)
        context['task_review'] = task_review
        return context

class ProjectTaskReviewForm(ModelForm):
    class Meta:
        model = ProjectTaskReview
        fields = ['public_reviewer_comments', 'private_reviewer_notes']


def process_task_review_request_view(request, proj_pk, task_pk, review_pk, action=None):
    project_task_review = get_project_task_review(request, proj_pk, task_pk, review_pk)
    if request.method == 'POST':
        form = ProjectTaskReviewForm(request.POST, instance=project_task_review)
        if form.is_valid():
            project_task_review = form.save(commit = False)
            try:
                if action == 'accept':
                    ProjectTaskService.accept_task_review(request.user, proj_pk, task_pk, project_task_review)
                    # messages.info(request, 'Membership request accepted.')
                else:
                    ProjectTaskService.reject_task_review(request.user, proj_pk, task_pk, project_task_review)
                    # messages.info(request, 'Membership request rejected.')
                return redirect('dssgmkt:proj_task_list', proj_pk=proj_pk)
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
                        {'project_task_review': project_task_review,
                        'breadcrumb': project_breadcrumb(project,
                                                            tasks_link(project),
                                                            ('Review completed task', None)),
                        'form': form,
                        }))


class ProjectTaskCancel(DeleteView):
    model = ProjectTaskRole
    template_name = 'dssgmkt/proj_task_cancel.html'

    def get_object(self):
        return get_own_project_task_role(self.request, self.kwargs['proj_pk'], self.kwargs['task_pk'])

    def get_success_url(self):
        return reverse('dssgmkt:proj_info', args=[self.object.task.project.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_task_role = self.object
        project_task = project_task_role.task
        project = project_task.project
        context['breadcrumb'] = project_breadcrumb(project,
                                                    volunteer_instructions_link(project),
                                                    ('Stop volunteering', None))
        add_project_task_common_context(self.request, project_task, 'instructions', context)
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


class ProjectTaskApply(CreateView):
    model = VolunteerApplication
    fields = ['volunteer_application_letter']
    template_name = 'dssgmkt/proj_task_apply.html'

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
            return HttpResponseRedirect(self.get_success_url())
        except KeyError:
            raise Http404


class ProjectTaskIndex(generic.ListView):
    model = ProjectTask
    template_name = 'dssgmkt/proj_task_list.html'
    context_object_name = 'project_tasks'

    def get_queryset(self):
        return ProjectTaskService.get_all_tasks(self.request.user, self.kwargs['proj_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project, tasks_link(project, include_link=False))
        add_project_common_context(self.request, project, 'tasklist', context)
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
        project = get_project(self.request, self.kwargs['proj_pk'])
        project_task = self.object
        context['breadcrumb'] = project_breadcrumb(project,
                                                    tasks_link(project),
                                                    ('Edit project task', None))
        add_project_task_common_context(self.request, project_task, 'tasklist', context)
        return context

    def form_valid(self, form):
        project_task = form.save(commit = False)
        try:
            ProjectTaskService.save_task(self.request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], project_task)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError:
            return super().form_invalid(form)


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
        project = get_project(self.request, self.kwargs['proj_pk'])
        context['breadcrumb'] = project_breadcrumb(project, ('Edit project information', None))
        add_project_common_context(self.request, project, 'info', context)
        return context

    def form_valid(self, form):
        project = form.save(commit = False)
        try:
            ProjectService.save_project(self.request.user, self.kwargs['proj_pk'], project)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError:
            return super().form_invalid(form)


class CreateTaskRequirementForm(ModelForm):
    class Meta:
        model = ProjectTaskRequirement
        fields = ['skill', 'level']

def project_task_requirements_edit_view(request, proj_pk, task_pk):
    ## TODO this is a security hole as anybody can post to this view and create new skills
    if request.method == 'POST':
        form = CreateTaskRequirementForm(request.POST)
        if form.is_valid():
            requirement = form.save(commit = False)
            try:
                ProjectTaskService.add_task_requirement(request.user, proj_pk, task_pk, requirement)
                return redirect('dssgmkt:proj_task_requirements_edit', proj_pk=proj_pk, task_pk=task_pk)
            except KeyError:
                form.add_error(None, "Invalid task requirement.")
    if request.method == 'GET':
        form = CreateTaskRequirementForm()
    task_requirements = get_project_task_requirements(request, proj_pk, task_pk)
    task = get_project_task(request, proj_pk, task_pk)
    project = get_project(request, proj_pk)
    return render(request, 'dssgmkt/proj_task_requirements_edit.html',
                    add_project_task_common_context(request, task, 'tasklist',
                        {
                            'task_requirements': task_requirements,
                            'breadcrumb': project_breadcrumb(project,
                                                                tasks_link(project),
                                                                edit_task_requirements_link(project, task, include_link=False)),
                            'add_requirement_form': form,
                        }))
    el

class ProjectTaskRequirementEdit(UpdateView):
    model = ProjectTaskRequirement
    fields = ['level']
    template_name = 'dssgmkt/proj_task_requirements_requirement_edit.html'
    pk_url_kwarg = 'requirement_pk'

    def get_success_url(self):
        return reverse('dssgmkt:proj_task_requirements_edit', args=[self.kwargs['proj_pk'], self.kwargs['task_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_requirement = self.object
        if task_requirement:
            project_task = task_requirement.task
            project = project_task.project
            context['task_requirement'] = task_requirement
            context['breadcrumb'] =  project_breadcrumb(project,
                                                            tasks_link(project),
                                                            edit_task_requirements_link(project, project_task),
                                                            ('Edit requirement', None))
            add_project_task_common_context(self.request, project_task, 'tasklist', context)
            return context
        else:
            raise Http404

    def form_valid(self, form):
        requirement = form.save(commit = False)
        try:
            ProjectTaskService.save_task_requirement(self.request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], requirement)
            return HttpResponseRedirect(self.get_success_url())
        except KeyError:
            return super().form_invalid(form)

class ProjectTaskRequirementRemove(DeleteView): # override the get_object / get_queryset method to use the domain logic
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
            context['task_requirement'] = task_requirement
            context['breadcrumb'] =  project_breadcrumb(project,
                                                            tasks_link(project),
                                                            edit_task_requirements_link(project, project_task),
                                                            ('Remove requirement', None))
            add_project_task_common_context(self.request, project_task, 'tasklist', context)
            return context
        else:
            raise Http404

    def delete(self, request,  *args, **kwargs):
        task_requirement = self.get_object()
        self.object = task_requirement
        try:
            ProjectTaskService.delete_task_requirement(request.user, self.kwargs['proj_pk'], self.kwargs['task_pk'], task_requirement)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as err:
            messages.error(request, 'There was a problem with your request.')
            # logger.error("Error when user {0} tried to leave organization {1}: {2}".format(request.user.id, organization_role.organization.id, err))
            return HttpResponseRedirect(self.get_success_url())

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
            context['breadcrumb'] =  project_breadcrumb(project,
                                                            tasks_link(project),
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


def create_default_project_task(request, proj_pk):
    if request.method == 'GET':
        raise Http404
    ## TODO this is a security hole as anybody can post to this view and create new skills
    elif request.method == 'POST':
        ProjectTaskService.create_default_task(request.user, proj_pk)
        return redirect('dssgmkt:proj_task_list', proj_pk = proj_pk)


class CreateProjectRoleForm(ModelForm):
    class Meta:
        model = ProjectRole
        fields = ['role', 'user']

def project_staff_view(request, proj_pk):
    ## TODO this is a security hole as staff can post to this view and create new members
    if request.method == 'POST':
        form = CreateProjectRoleForm(request.POST)
        if form.is_valid:
            project_role = form.save(commit = False)
            try:
                ProjectService.add_staff_member(request.user, proj_pk, project_role)
                messages.info(request, 'Staff member added successfully.')
                return redirect('dssgmkt:proj_staff', proj_pk = proj_pk)
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


def project_volunteers_view(request, proj_pk):
    if request.method == 'GET':
        project = get_project(request, proj_pk)

        volunteers = ProjectService.get_all_project_volunteers(request.user, proj_pk)
        volunteers_page = paginate(request, volunteers, request_key='volunteers_page', page_size=20)

        volunteer_applications = ProjectService.get_all_volunteer_applications(request.user, proj_pk)
        applications_page = paginate(request, volunteer_applications, request_key='applications_page', page_size=1)

        return render(request, 'dssgmkt/proj_volunteers.html',
                        add_project_common_context(request, project, 'volunteers',
                            {
                                'breadcrumb': project_breadcrumb(project, ('Volunteers', None)),
                                'volunteers': volunteers_page,
                                'volunteer_applications': applications_page,
                            }))


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
        except KeyError:
            return super().form_invalid(form)

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
            context['breadcrumb'] =  project_breadcrumb(project,
                                                        staff_link(project),
                                                        ('Remove staff member', None))
            add_project_common_context(self.request, project, 'staff', context)
            return context
        else:
            raise Http404

    def delete(self, request,  *args, **kwargs):
        project_role = self.get_object()
        self.object = project_role
        try:
            ProjectService.delete_project_role(request.user, self.kwargs['proj_pk'], project_role)
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as err:
            messages.error(request, 'There was a problem with your request.')
            # logger.error("Error when user {0} tried to leave organization {1}: {2}".format(request.user.id, organization_role.organization.id, err))
            return HttpResponseRedirect(self.get_success_url())

class EditProjectTaskRoleForm(ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(EditProjectTaskRoleForm, self).__init__(*args, **kwargs)
        self.fields['task'].queryset = ProjectTaskService.get_non_finished_tasks(user, self.instance.task.project)

    class Meta:
        model = ProjectTaskRole
        fields = ['task']

class ProjectTaskRoleEdit(SuccessMessageMixin, UpdateView):
    model = ProjectTaskRole
    form_class = EditProjectTaskRoleForm
    template_name = 'dssgmkt/proj_task_volunteer_edit.html'
    pk_url_kwarg = 'task_role_pk'
    success_message = 'Volunteer edited successfully'

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

class ProjectTaskRoleRemove(DeleteView):
    model = ProjectTaskRole
    template_name = 'dssgmkt/proj_volunteer_remove.html'

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

class VolunteerApplicationReviewForm(ModelForm):

    class Meta:
        model = VolunteerApplication
        fields = ['public_reviewer_comments', 'private_reviewer_notes']

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
                                'form': form,
                            }))
    else:
        raise Http404


def follow_project_view(request, proj_pk):
    if request.method == 'GET':
        raise Http404
    ## TODO this is a security hole as anybody can post to this view and create new skills
    elif request.method == 'POST':
        try:
            ProjectService.toggle_follower(request.user, proj_pk)
            return redirect('dssgmkt:proj_info', proj_pk=proj_pk)
        except KeyError:
            messages.error(request, 'There was an error while processing your request.')
            return redirect('dssgmkt:proj_info', proj_pk=proj_pk)
