from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, render
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from rules.contrib.views import (
    PermissionRequiredMixin, objectgetter, permission_required,
)

from ..models.user import VolunteerProfile
from .common import build_breadcrumb, home_link, paginate

from marketplace.domain.user import UserService


def admin_link(include_link=True):
    return ('Admin', reverse_lazy('marketplace:admin_home') if include_link else None)


class AdminHomeView(PermissionRequiredMixin, generic.ListView):
    model = VolunteerProfile
    template_name = 'dssgmkt/admin_home.html'
    context_object_name = 'volunteer_profiles'
    paginate_by = 30
    permission_required = 'volunteer.new_user_review'
    raise_exception = True
    allow_empty = True

    def get_queryset(self):
        return UserService.get_pending_volunteer_profiles(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb'] = build_breadcrumb([home_link(), admin_link()])
        return context

    def get_permission_object(self):
        return self.request.user


def get_request_user(request, volunteer_pk, action):
    return request.user

@permission_required('volunteer.new_user_review', raise_exception=True, fn=get_request_user)
def review_volunteer_profile_view(request, volunteer_pk, action):
    if request.method == 'GET':
        raise Http404
    elif request.method == 'POST':
        try:
            if action == 'accept':
                UserService.accept_volunteer_profile(request.user, volunteer_pk)
            else:
                UserService.reject_volunteer_profile(request.user, volunteer_pk)
            return redirect('marketplace:admin_home')
        except KeyError as k:
            messages.error(request, str(k))
            return redirect('marketplace:admin_home')
