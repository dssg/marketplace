from importlib import import_module

from allauth.socialaccount import providers


# Note: This is not the documented manner of installing allauth paths.
# Rather, for example, you might:
#
#     path('accounts/', include('allauth.urls')),
#
# (And you certainly don't need a separate urls module for that purpose.)
#
# However, that installs all of allauth's account-handling controllers.
# For now, we only need OAuth provider URLs.
#
# So instead, we use this module to cleanly define just the provider paths,
# and then include these as needed.
#
# https://django-allauth.readthedocs.io/en/latest/installation.html
#
# See also: marketplace.socialauth.account_urls


urlpatterns = []

for provider in providers.registry.get_list():
    try:
        prov_mod = import_module(provider.get_package() + '.urls')
    except ImportError:
        pass
    else:
        prov_urlpatterns = getattr(prov_mod, 'urlpatterns', ())
        urlpatterns.extend(prov_urlpatterns)
