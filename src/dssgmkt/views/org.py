from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.paginator import Paginator
from django.forms import ModelForm
from django.db.models import Case, When, Q
from django.core.exceptions import ValidationError
from django.contrib.messages.views import SuccessMessageMixin
from datetime import date

from ..models.common import (NEW, ORGANIZATION_STAFF, ACCEPTED, REJECTED)
from ..models.org import (Organization, OrganizationRole, OrganizationMembershipRequest)
from ..authorization.org import is_organization_admin
from rules.contrib.views import permission_required, objectgetter, PermissionRequiredMixin
from .common import home_link, build_breadcrumb

def organizations_link(include_link=True):
    return ('Organizations', reverse('dssgmkt:org_list') if include_link else None)

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
