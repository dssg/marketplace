from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
@stringfilter
def wordbreak(value, at):
    """Insert `<wbr>` after each occurence of `at`.

    Facilitates legible breaking of `value` across lines.

    """
    return mark_safe(value.replace(at, f'{at}<wbr>'))
