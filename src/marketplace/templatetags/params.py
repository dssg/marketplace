"""template tags interacting with the request's query parameters"""
from django import template


register = template.Library()



@register.simple_tag(takes_context=True)
def set_params(context, *interleaved, **pairs):
    """construct a copy of the current request's query parameters,
    updated with the given parameters.

    parameter keys and values may be specified either as named keyword
    argument pairs:

        set_params query='cookie' page=2

    and/or as interleaved keys and values (permitting the template
    language to specify variable keys):

        set_params querykey 'cookie' pagekey nextpage

    (which might evaluate as):

        set_params 'query' 'cookie' 'page' 2

    """
    request = context['request']
    params = request.GET.copy()

    while interleaved:
        try:
            (key, value, *interleaved) = interleaved
        except ValueError:
            raise TypeError('incorrect number of arguments for interleaved parameter pairs')

        params[key] = value

    params.update(pairs)

    return params.urlencode()


@register.simple_tag(takes_context=True)
def set_params_path(context, *interleaved, **pairs):
    """construct the current full path (including query), updated by the
    given parameters.

    (See: ``set_params``.)

    """
    request = context['request']
    params = set_params(context, *interleaved, **pairs)
    return request.path + '?' + params
