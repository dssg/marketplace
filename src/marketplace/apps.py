import importlib

from django.apps import AppConfig


class MarketplaceConfig(AppConfig):

    name = 'marketplace'
    verbose_name = 'Solve for Good'

    def ready(self):
        # marketplace.domain contains signal-connections, so ensure it
        # is (eagerly) imported, as soon as the app is ready (loaded)
        importlib.import_module('marketplace.domain')
