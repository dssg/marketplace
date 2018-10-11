import urllib.parse

import django.forms
import django.shortcuts


def redirect(*args, params=None, **kwargs):
    response = django.shortcuts.redirect(*args, **kwargs)
    if params is not None:
        response['Location'] += '?' + urllib.parse.urlencode(params)
    return response


class SubmitSelect(django.forms.widgets.ChoiceWidget):

    input_type = 'submit'
    template_name = 'django/forms/widgets/multiple_input.html'
    option_template_name = 'marketplace/widgets/button.html'
