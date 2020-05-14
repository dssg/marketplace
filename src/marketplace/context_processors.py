from django.conf import settings


def ga_tracking_id(request):
    return {} if settings.DEBUG else {'GA_TRACKING_ID': settings.GA_TRACKING_ID}
