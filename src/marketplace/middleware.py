from marketplace import utils


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
