from datetime import date

from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Case, Q, When
from django.forms import ModelForm
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from rules.contrib.views import (
    PermissionRequiredMixin, objectgetter, permission_required,
)

from ..models.common import ReviewStatus, OrgRole
from ..models.org import (
    Organization, OrganizationMembershipRequest, OrganizationRole,
)
from dssgmkt.domain.org import OrganizationService
from .common import build_breadcrumb, home_link, paginate


def organizations_link(include_link=True):
    return ('Organizations', reverse('dssgmkt:org_list') if include_link else None)

def organization_link(organization, include_link=True):
    return (organization.name, reverse('dssgmkt:org_info', args=[organization.id]) if include_link else None)

def organization_staff_link(organization, include_link=True):
    return ('Staff', reverse('dssgmkt:org_staff', args=[organization.id]) if include_link else None)

def organization_membership_request_link(membership_request, include_link=True):
    return ('Membership request', reverse('dssgmkt:org_staff_request_detail',
                                            args=[membership_request.organization.id, membership_request.id ]) if include_link else None)

def organization_breadcrumb(organization, *items):
    breadcrumb_items = [home_link(),
                        organizations_link(),
                        organization_link(organization, items)]
    breadcrumb_items += items
    return build_breadcrumb(breadcrumb_items)


def get_organization(request, org_pk):
    organization = OrganizationService.get_organization(request.user, org_pk)
    if organization:
        return organization
    else:
        raise Http404

def get_organization_membership_request(request, request_pk):
    membership_request = OrganizationService.get_organization_membership_request(request.user, request_pk)
    if membership_request:
        return membership_request
    else:
        raise Http404

def get_organization_role(request, org_pk, user_pk):
    role = OrganizationService.get_organization_role(request.user, org_pk, user_pk)
    if role:
        return role
    else:
        raise Http404


class OrganizationIndexView(generic.ListView):
    template_name = 'dssgmkt/org_list.html'
    context_object_name = 'org_list'
    paginate_by = 1

    def get_queryset(self):
        # This gets paginated by the view so we are not retrieving all the organizations in one query
        return OrganizationService.get_all_organizations(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = build_breadcrumb([home_link(),
                                                  organizations_link(False)])
        return context

def add_organization_user_context(request, context, user, organization):
    if not user.is_anonymous:
        context['user_is_staff'] = OrganizationService.user_is_organization_staff(user, organization)
        context['user_is_administrator'] = OrganizationService.user_is_organization_admin(user, organization)
        context['user_is_member'] = OrganizationService.user_is_organization_member(user, organization)
    return context

class OrganizationView(generic.DetailView):
    model = Organization
    template_name = 'dssgmkt/org_info.html'
    pk_url_kwarg = 'org_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization_tab'] = 'info'
        context['breadcrumb'] = organization_breadcrumb(self.object)

        projects = self.object.project_set.all() # TODO move this query to the project domain
        context['projects'] = paginate(self.request, projects, request_key='projects_page', page_size=25)

        add_organization_user_context(self.request, context, self.request.user, self.object)
        context['user_is_pending_membership'] = OrganizationService.user_is_pending_membership(self.request.user, self.object)

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
        organization = get_organization(self.request, self.kwargs['org_pk'])
        context['organization'] = organization
        context['breadcrumb'] = organization_breadcrumb(organization,
                                                        ('Edit information', None))
        context['organization_tab']='info'
        add_organization_user_context(self.request, context, self.request.user, organization)
        return context


class CreateOrganizationRoleForm(ModelForm):
    class Meta:
        model = OrganizationRole
        fields = ['role', 'user']

@permission_required('organization.staff_view', fn=objectgetter(Organization, 'org_pk'))
def organization_staff_view(request, org_pk):
## TODO this is a security hole as staff can post to this view and create new members
    if request.method == 'POST':
        form = CreateOrganizationRoleForm(request.POST)
        if form.is_valid():
            organization_role = form.save(commit = False)
            try:
                OrganizationService.add_staff_member(request.user, org_pk, organization_role)
                messages.info(request, 'Staff member added successfully.')
                return redirect('dssgmkt:org_staff', org_pk=org_pk)
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

    return render(request, 'dssgmkt/org_staff.html',
                    add_organization_user_context(
                        request,
                        {'organization': organization,
                        'organization_tab': 'staff',
                        'breadcrumb': organization_breadcrumb(organization, ('Staff', None)),
                        'organization_staff': staff_page,
                        'organization_requests': requests_page,
                        'add_staff_form': form,
                        }, request.user, organization))



class OrganizationMembershipRequestCreate(CreateView):
    model = OrganizationMembershipRequest
    fields = []
    template_name = 'dssgmkt/org_staff_request.html'

    def get_success_url(self):
        return reverse('dssgmkt:org_info', args=[self.kwargs['org_pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = get_organization(self.request, self.kwargs['org_pk'])
        context['organization'] = organization
        context['breadcrumb'] = organization_breadcrumb(organization,
                                                        ('Request membership', None))
        context['organization_tab']='info'
        add_organization_user_context(self.request, context, self.request.user, organization)
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

class OrganizationMembershipRequestView(PermissionRequiredMixin, generic.DetailView):
    model = OrganizationMembershipRequest
    template_name = 'dssgmkt/org_staff_request_detail.html'
    pk_url_kwarg = 'request_pk'
    permission_required = 'organization.membership_request_view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        membership_request = self.object
        organization = membership_request.organization
        context['organization'] = organization
        context['organization_tab'] = 'staff'
        context['breadcrumb'] = organization_breadcrumb(organization,
                                                        organization_staff_link(organization),
                                                        ('Membership request', None))
        add_organization_user_context(self.request, context, self.request.user, organization)
        return context

class OrganizationMembershipRequestForm(ModelForm):
    class Meta:
        model = OrganizationMembershipRequest
        fields = ['role', 'public_reviewer_comments', 'private_reviewer_notes']


@permission_required('organization.membership_review', fn=objectgetter(OrganizationMembershipRequest, 'request_pk'))
def process_organization_membership_request_view(request, org_pk, request_pk, action=None):
    membership_request = get_organization_membership_request(request, request_pk)
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
                return redirect('dssgmkt:org_staff', org_pk=org_pk)
            except KeyError:
                raise Http404
    elif request.method == 'GET':
        form = OrganizationMembershipRequestForm()
    organization = get_organization(request, org_pk)

    return render(request, 'dssgmkt/org_staff_request_review.html',
                    add_organization_user_context(
                        request,
                        {'organization': organization,
                        'organizationmembershiprequest': membership_request,
                        'organization_tab': 'staff',
                        'breadcrumb': organization_breadcrumb(organization,
                                                                organization_staff_link(organization),
                                                                organization_membership_request_link(membership_request),
                                                                ('Review request', None)),
                        'form': form,
                        }, request.user, organization))


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
            organization = self.object.organization
            context['organization'] = organization
            context['breadcrumb'] = organization_breadcrumb(organization,
                                                            organization_staff_link(organization),
                                                            ('Edit', None))
            context['organization_tab']='staff'
            add_organization_user_context(self.request, context, self.request.user, organization)
            return context
        else:
            raise Http404

    def form_valid(self, form):
        organization_role = form.save(commit = False)
        try:
            OrganizationService.save_organization_role(self.request.user, self.kwargs['org_pk'], organization_role)
            messages.info(self.request, 'User role edited successfully.')
            return HttpResponseRedirect(self.get_success_url())
        except ValueError:
            return super().form_invalid(form)



class OrganizationLeave(PermissionRequiredMixin, DeleteView):
    model = OrganizationRole
    template_name = 'dssgmkt/org_staff_leave.html'
    permission_required = 'organization.membership_leave'

    def get_object(self):
        return get_organization_role(self.request, self.kwargs['org_pk'], self.request.user.id)

    def get_success_url(self):
        return reverse('dssgmkt:org_info', args=[self.object.organization.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization_role = self.object
        if organization_role and organization_role.organization.id == self.kwargs['org_pk']:
            organization = self.object.organization
            context['organization'] = organization
            context['breadcrumb'] = organization_breadcrumb(organization,
                                                            ('Leave organization', None))
            context['organization_tab']='info'
            add_organization_user_context(self.request, context, self.request.user, organization)
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
        except ValueError:
            messages.error(request, 'There was a problem with your request.') ## TODO log the exception
            return HttpResponseRedirect(self.get_success_url())

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
            organization = self.object.organization
            context['organization'] = organization
            context['breadcrumb'] = organization_breadcrumb(organization,
                                                            organization_staff_link(organization),
                                                            ('Remove staff member', None))
            context['organization_tab']='staff'
            add_organization_user_context(self.request, context, self.request.user, organization)
            return context
        else:
            raise Http404

    def delete(self, request,  *args, **kwargs):
        organization_role = self.get_object()
        self.object = organization_role
        try:
            OrganizationService.delete_organization_role(request.user, self.kwargs['org_pk'], organization_role)
            messages.info(request, 'Staff member removed successfully.')
            return HttpResponseRedirect(self.get_success_url())
        except ValueError:
            messages.error(request, 'There was a problem with your request.') ## TODO log the exception
            return HttpResponseRedirect(self.get_success_url())
