from itertools import repeat, zip_longest

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator


def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'marketplace/home_user.html')
    else:
        return render(request, 'marketplace/home_anonymous.html')

def about_view(request):
    return render(request, 'marketplace/about.html')

def resources_view(request):
    return render(request, 'marketplace/resources.html')

def home_link(include_link=True):
    return ('Home', reverse_lazy('marketplace:home') if include_link else None)

def build_breadcrumb(elements):
    # return [val for pair in zip_longest(elements, repeat((' > ', None), len(elements) - 1)) for val in pair if val is not None]
    return elements


def paginate(request, query_set, page_size=25, request_key='page'):
    paginator = Paginator(query_set, page_size)
    return paginator.get_page(request.GET.get(request_key, 1))


def generic_getter(domain_function, *args):
    try:
        result_object = domain_function(*args)
    except Exception as e:
        result_object = None
    if result_object:
        return result_object
    else:
        raise Http404
