from datetime import date

from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Case, Q, When
from django.forms import ModelForm
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from rules.contrib.views import (
    PermissionRequiredMixin, objectgetter, permission_required,
)
import logging

from ..models.common import ReviewStatus, OrgRole
from ..models.org import (
    Organization, OrganizationMembershipRequest, OrganizationRole,
)
from marketplace.domain.org import OrganizationService
from marketplace.domain.common import get_social_causes
from .common import build_breadcrumb, home_link, paginate, generic_getter


logger = logging.getLogger(__name__)

def organizations_link(include_link=True):
    return ('Organizations', reverse('marketplace:org_list') if include_link else None)

def organization_link(organization, include_link=True):
    return (organization.name, reverse('marketplace:org_info', args=[organization.id]) if include_link else None)

def organization_staff_link(organization, include_link=True):
    return ('Staff', reverse('marketplace:org_staff', args=[organization.id]) if include_link else None)

def organization_membership_request_link(membership_request, include_link=True):
    return ('Membership request', reverse('marketplace:org_staff_request_review',
                                            args=[membership_request.organization.id, membership_request.id ]) if include_link else None)

def organization_breadcrumb(organization, *items):
    breadcrumb_items = [home_link(),
                        organizations_link(),
                        organization_link(organization, items)]
    breadcrumb_items += items
    return build_breadcrumb(breadcrumb_items)


def get_organization(request, org_pk):
    return generic_getter(OrganizationService.get_organization,request.user, org_pk)

def get_organization_membership_request(request, org_pk, request_pk):
    return generic_getter(OrganizationService.get_organization_membership_request, request.user, org_pk, request_pk)

def get_organization_role(request, org_pk, user_pk):
    return generic_getter(OrganizationService.get_organization_role, request.user, org_pk, user_pk)

def get_organization_role_by_pk(request, org_pk, role_pk):
    return generic_getter(OrganizationService.get_organization_role_by_pk, request.user, org_pk, role_pk)


def organization_list_view(request):
    checked_social_cause_fields = {}
    checked_project_fields = {}
    filter_orgname = ""
    if request.method == 'POST':
        search_config = {}
        if 'orgname' in request.POST and request.POST.get('orgname'):
            search_config['name'] = request.POST.get('orgname')
            filter_orgname = request.POST.get('orgname')
        if 'socialcause' in request.POST:
            search_config['social_cause'] = request.POST.getlist('socialcause')
            for f in request.POST.getlist('socialcause'):
                checked_social_cause_fields[f] = True
        if 'projectstatus' in request.POST:
            search_config['project_status'] = request.POST.getlist('projectstatus')
            for f in request.POST.getlist('projectstatus'):
                checked_project_fields[f] = True
        organizations = OrganizationService.get_all_organizations(request.user, search_config)
    elif request.method == 'GET':
        organizations = OrganizationService.get_all_organizations(request.user)

    if organizations:
        organizations_page = paginate(request, organizations, page_size=15)
    else:
        organizations_page = []

    return render(request, 'marketplace/org_list.html',
                        {
                            'breadcrumb': build_breadcrumb([home_link(), organizations_link(False)]),
                            'org_list': organizations_page,
                            'checked_social_cause_fields': checked_social_cause_fields,
                            'checked_project_fields': checked_project_fields,
                            'filter_orgname': filter_orgname
                        })

def add_organization_common_context(request, organization, page_tab, context):
    context['organization'] = organization
    context['page_tab'] = page_tab
    if not request.user.is_anonymous:
        context['user_is_staff'] = OrganizationService.user_is_organization_staff(request.user, organization)
        context['user_is_administrator'] = OrganizationService.user_is_organization_admin(request.user, organization)
        context['user_is_member'] = OrganizationService.user_is_organization_member(request.user, organization)
    return context

class OrganizationView(generic.DetailView):
    model = Organization
    template_name = 'marketplace/org_info.html'
    pk_url_kwarg = 'org_pk'

    def get_object(self):
        return get_organization(self.request, self.kwargs['org_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = organization_breadcrumb(self.object)
        organization = self.object

        projects = OrganizationService.get_organization_projects(self.request.user, organization)
        context['projects'] = paginate(self.request, projects, request_key='projects_page', page_size=25)

        add_organization_common_context(self.request, self.object, 'info', context)
        context['user_is_pending_membership'] = OrganizationService.user_is_pending_membership(self.request.user, organization)

        return context

class EditOrganizationForm(ModelForm):
    class Meta:
        model = Organization
        exclude = ['logo_url', 'main_cause']

class OrganizationEdit(PermissionRequiredMixin, UpdateView):
    model = Organization
    form_class = EditOrganizationForm
    template_name = 'marketplace/org_info_edit.html'
    pk_url_kwarg = 'org_pk'
    permission_required = 'organization.information_edit'
    raise_exception = True

    def get_success_url(self):
        return reverse('marketplace:org_info', args=[self.kwargs['org_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = get_organization(self.request, self.kwargs['org_pk'])
        context['organization'] = organization
        context['breadcrumb'] = organization_breadcrumb(organization,
                                                        ('Edit information', None))
        social_causes = []
        for sc in get_social_causes():
            sc_value, sc_name = sc
            selected = organization.organizationsocialcause_set.filter(social_cause=sc_value).exists()
            social_causes.append({'social_cause_text': sc_name, 'social_cause_value': sc_value, 'selected': selected})
        context['social_causes'] = social_causes

        add_organization_common_context(self.request, organization, 'info', context)
        return context

    def form_valid(self, form):
        organization = form.save(commit = False)
        try:
            OrganizationService.save_organization_info(self.request.user, self.kwargs['org_pk'], organization)
            OrganizationService.save_organization_social_causes(self.request.user, self.kwargs['org_pk'], organization, self.request.POST)
            return HttpResponseRedirect(self.get_success_url())
        except KeyError as k:
            form.add_error(None, str(k))
            return super().form_invalid(form)

class CreateOrganizationRoleForm(ModelForm):
    class Meta:
        model = OrganizationRole
        fields = ['role', 'user']

@permission_required('organization.staff_view', raise_exception=True, fn=objectgetter(Organization, 'org_pk'))
def organization_staff_view(request, org_pk):
    if request.method == 'POST':
        form = CreateOrganizationRoleForm(request.POST)
        if form.is_valid():
            organization_role = form.save(commit = False)
            try:
                OrganizationService.add_staff_member(request.user, org_pk, organization_role)
                messages.info(request, 'Staff member added successfully.')
                return redirect('marketplace:org_staff', org_pk=org_pk)
            except KeyError:
                raise Http404
            except ValueError:
                form.add_error(None, "This user is already a member of the organization.")
    elif request.method == 'GET':
        form = CreateOrganizationRoleForm()
    organization = get_organization(request, org_pk)

    organization_staff = OrganizationService.get_organization_staff(request.user, organization)
    staff_page = paginate(request, organization_staff, request_key='staff_page', page_size=25)

    organization_requests = OrganizationService.get_membership_requests(request.user, organization)
    requests_page = paginate(request, organization_requests, request_key='requests_page', page_size=25)

    return render(request, 'marketplace/org_staff.html',
                    add_organization_common_context(
                        request,
                        organization,
                        'staff',
                        {'breadcrumb': organization_breadcrumb(organization, ('Staff', None)),
                        'organization_staff': staff_page,
                        'organization_requests': requests_page,
                        'add_staff_form': form,
                        'organization_roles': OrganizationService.get_organization_roles(),
                        }))


@permission_required('organization.staff_view', raise_exception=True, fn=objectgetter(Organization, 'org_pk'))
def add_organization_staff_view(request, org_pk):
    if request.method == 'POST':
        form_errors = []
        userid = request.POST.get('userid')
        role = request.POST.get('role')
        if userid and role:
            try:
                OrganizationService.add_staff_member_by_id(request.user, org_pk, userid, role)
                messages.info(request, 'Staff member added successfully.')
                return redirect('marketplace:org_staff', org_pk=org_pk)
            except ValueError as v:
                form_errors.append(str(v))
            except KeyError as k:
                form_errors.append(str(k))
        else:
            if not userid:
                form_errors.append('Plese select a user to add to the organization.')
            if not role:
                form_errors.append('Plese select a role for the user.')


    organization = get_organization(request, org_pk)
    organization_staff = OrganizationService.get_organization_staff(request.user, organization)
    staff_page = paginate(request, organization_staff, request_key='staff_page', page_size=25)

    organization_requests = OrganizationService.get_membership_requests(request.user, organization)
    requests_page = paginate(request, organization_requests, request_key='requests_page', page_size=25)
    return render(request, 'marketplace/org_staff.html',
                    add_organization_common_context(
                        request,
                        organization,
                        'staff',
                        {'breadcrumb': organization_breadcrumb(organization, ('Staff', None)),
                        'organization_staff': staff_page,
                        'organization_requests': requests_page,
                        'organization_roles': OrganizationService.get_organization_roles(),
                        'form_errors': form_errors,
                        }))

class OrganizationMembershipRequestCreate(CreateView):
    model = OrganizationMembershipRequest
    fields = []
    template_name = 'marketplace/org_staff_request.html'

    def get_success_url(self):
        return reverse('marketplace:org_info', args=[self.kwargs['org_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = get_organization(self.request, self.kwargs['org_pk'])
        context['breadcrumb'] = organization_breadcrumb(organization,
                                                        ('Request membership', None))
        add_organization_common_context(self.request, organization, 'info', context)
        return context

    def form_valid(self, form):
        membership_request = form.save(commit=False)
        try:
            OrganizationService.create_membership_request(self.request.user, self.request.user, self.kwargs['org_pk'], membership_request)
            messages.info(self.request,
                          'Membership request for '+ membership_request.organization.name +' successful. You will be notifed when the administrators make a decision about your membership.')
            return HttpResponseRedirect(self.get_success_url())
        except KeyError:
            raise Http404

class OrganizationMembershipRequestForm(ModelForm):
    class Meta:
        model = OrganizationMembershipRequest
        fields = ['role', 'public_reviewer_comments', 'private_reviewer_notes']


@permission_required('organization.membership_review', raise_exception=True, fn=objectgetter(OrganizationMembershipRequest, 'request_pk'))
def process_organization_membership_request_view(request, org_pk, request_pk, action=None):
    membership_request = get_organization_membership_request(request, org_pk, request_pk)
    if request.method == 'POST':
        form = OrganizationMembershipRequestForm(request.POST, instance=membership_request)
        if form.is_valid():
            membership_request = form.save(commit = False)
            try:
                if action == 'accept':
                    OrganizationService.accept_membership_request(request.user, org_pk, membership_request)
                    messages.info(request, 'Membership request accepted.')
                else:
                    OrganizationService.reject_membership_request(request.user, org_pk, membership_request)
                    messages.info(request, 'Membership request rejected.')
                return redirect('marketplace:org_staff', org_pk=org_pk)
            except KeyError:
                raise Http404
    elif request.method == 'GET':
        form = OrganizationMembershipRequestForm()
    organization = get_organization(request, org_pk)

    return render(request, 'marketplace/org_staff_request_review.html',
                    add_organization_common_context(
                        request,
                        organization,
                        'staff',
                        {'organizationmembershiprequest': membership_request,
                        'breadcrumb': organization_breadcrumb(organization,
                                                                organization_staff_link(organization),
                                                                organization_membership_request_link(membership_request, include_link=False)),
                        'form': form,
                        }))


class OrganizationRoleEdit(PermissionRequiredMixin, UpdateView):
    model = OrganizationRole
    fields = ['role']
    template_name = 'marketplace/org_staff_edit.html'
    pk_url_kwarg = 'role_pk'
    permission_required = 'organization.role_edit'
    raise_exception = True

    def get_success_url(self):
        return reverse('marketplace:org_staff', args=[self.object.organization.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization_role = self.object
        if organization_role and organization_role.organization.id == self.kwargs['org_pk']:
            organization = self.object.organization
            context['breadcrumb'] = organization_breadcrumb(organization,
                                                            organization_staff_link(organization),
                                                            ('Edit', None))
            add_organization_common_context(self.request, organization, 'staff', context)
            return context
        else:
            raise Http404

    def form_valid(self, form):
        organization_role = form.save(commit = False)
        try:
            OrganizationService.save_organization_role(self.request.user, self.kwargs['org_pk'], organization_role)
            messages.info(self.request, 'User role edited successfully.')
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as v:
            form.add_error(None, str(v))
            return super().form_invalid(form)



class OrganizationLeave(PermissionRequiredMixin, DeleteView):
    model = OrganizationRole
    template_name = 'marketplace/org_staff_leave.html'
    permission_required = 'organization.membership_leave'
    raise_exception = True

    def get_object(self):
        return get_organization_role(self.request, self.kwargs['org_pk'], self.request.user.id)

    def get_success_url(self):
        return reverse('marketplace:org_info', args=[self.object.organization.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization_role = self.object
        if organization_role and organization_role.organization.id == self.kwargs['org_pk']:
            organization = self.object.organization
            context['breadcrumb'] = organization_breadcrumb(organization,
                                                            ('Leave organization', None))
            add_organization_common_context(self.request, organization, 'info', context)
            return context
        else:
            raise Http404

    def delete(self, request,  *args, **kwargs):
        organization_role = self.get_object()
        self.object = organization_role
        try:
            OrganizationService.leave_organization(request.user, self.kwargs['org_pk'], organization_role)
            messages.info(request, 'You left ' + organization_role.organization.name + ' successfully.')
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as err:
            messages.error(request, 'There was a problem with your request.')
            logger.error("Error when user {0} tried to leave organization {1}: {2}".format(request.user.id, organization_role.organization.id, err))
            return HttpResponseRedirect(self.get_success_url())

class DeleteOrganizationRoleForm(ModelForm):
    class Meta:
        model = OrganizationRole
        fields = []

@permission_required('organization.role_delete', raise_exception=True, fn=objectgetter(OrganizationRole, 'role_pk'))
def organization_role_delete_view(request, org_pk, role_pk):
    organization_role = get_organization_role_by_pk(request, org_pk, role_pk)
    if request.method == 'POST':
        form = DeleteOrganizationRoleForm(request.POST)
        if form.is_valid():
            try:
                OrganizationService.delete_organization_role(request.user, org_pk, organization_role)
                messages.info(request, 'Staff member removed successfully.')
                return redirect('marketplace:org_staff', org_pk=org_pk)
            except KeyError:
                raise Http404
            except ValueError as err:
                logger.error("Error when trying to remove user {0} from organization {1}: {2}".format(request.user.id, organization_role.organization.id, err))
                form.add_error(None, str(err))
    elif request.method == 'GET':
        form = DeleteOrganizationRoleForm()
    organization = get_organization(request, org_pk)
    return render(request, 'marketplace/org_staff_remove.html',
                    add_organization_common_context(request, organization, 'staff',
                        {
                            'organizationrole': organization_role,
                            'breadcrumb': organization_breadcrumb(organization,
                                                                    organization_staff_link(organization),
                                                                    ('Remove staff member', None)),
                            'form': form,
                        }))


class CreateOrganizationForm(ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'short_summary', 'description', 'logo_file', 'website_url', 'phone_number',
                'email_address', 'street_address', 'address_line_2', 'city', 'state',
                'zipcode', 'country', 'budget', 'years_operation',
                'organization_scope',]

class OrganizationCreateView(PermissionRequiredMixin, CreateView):
    model = Organization
    form_class = CreateOrganizationForm
    template_name = 'marketplace/org_create.html'
    permission_required = 'organization.create'
    raise_exception = True

    def get_success_url(self):
        return reverse('marketplace:org_info', args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = [home_link(), organizations_link(), ('Create new organization', None)]
        social_causes = []
        for sc in get_social_causes():
            sc_value, sc_name = sc
            social_causes.append({'social_cause_text': sc_name, 'social_cause_value': sc_value, 'selected': False})
        context['social_causes'] = social_causes
        return context

    def form_valid(self, form):
        organization = form.save(commit=False)
        try:
            organization = OrganizationService.create_organization(self.request.user, organization)
            OrganizationService.save_organization_social_causes(self.request.user, organization.id, organization, self.request.POST)
            messages.info(self.request, "You have created a new organization and are now its first administrator user.")
            self.object = organization
            return HttpResponseRedirect(self.get_success_url())
        except KeyError:
            raise Http404
        except ValueError as v:
            form.add_error(None, str(v))
            return self.form_invalid(form)

    def get_permission_object(self):
        return None



def get_all_users_not_organization_members_json(request, org_pk, query=None):
    users = OrganizationService.get_all_users_not_organization_members(org_pk, query)
    json_users = []
    for user in users:
        json_users.append({'name':user['first_name'] + " " + user['last_name'] + " (" + user['username'] + ")", 'id': str(user['id'])})
    data = {
        'users': json_users
    }
    return JsonResponse(data)
