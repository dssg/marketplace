from django.conf import settings

def ga_tracking_id(request):
    if settings.DEBUG is False:
        return {'GA_TRACKING_ID': settings.GA_TRACKING_ID}
    else:
        return {}
