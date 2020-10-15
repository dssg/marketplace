from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

from marketplace import utils


def version_header_middleware(get_response):
    """Decorate response with software application version header."""
    if getattr(settings, 'APP_VERSION', None) is None:
        raise MiddlewareNotUsed

    app_version = settings.APP_VERSION or '<unversioned>'

    def middleware(request):
        response = get_response(request)
        response['Software'] = f'marketplace/{app_version}'
        return response

    return middleware


class UserTypeMiddleware:

    selector_url_name = 'marketplace:user_type_select'

    def __init__(self, next_handler):
        self.next_handler = next_handler

    def __call__(self, request):
        return self.next_handler(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated and request.user.initial_type is None:
            if ':' in self.selector_url_name:
                url_name = f'{request.resolver_match.namespace}:{request.resolver_match.url_name}'
            else:
                url_name = request.resolver_match.url_name

            if url_name != self.selector_url_name:
                return utils.redirect(
                    self.selector_url_name,
                    params={'next': request.get_full_path()},
                )
