from itertools import repeat, zip_longest

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse


def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'dssgmkt/home_user.html')
    else:
        return render(request, 'dssgmkt/home_anonymous.html')

def about_view(request):
    return render(request, 'dssgmkt/about.html')

def home_link(include_link=True):
    return ('Home', reverse('dssgmkt:home') if include_link else None)

def build_breadcrumb(elements):
    return [val for pair in zip_longest(elements, repeat((' > ', None), len(elements) - 1)) for val in pair if val is not None]
