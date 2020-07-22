from django.conf import settings


Empty = object()


INCLUDED_SETTINGS = getattr(settings, 'TEMPLATE_INCLUDED_SETTINGS', ())


def include_settings(request):
    values = (
        getattr(settings, name, Empty)
        for name in INCLUDED_SETTINGS
    )
    return {
        'settings': {
            name: value
            for (name, value) in zip(INCLUDED_SETTINGS, values)
            if value is not Empty
        }
    }
