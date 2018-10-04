import importlib

from django.apps import AppConfig


class MarketplaceConfig(AppConfig):

    name = 'marketplace'
    verbose_name = 'Solve for Good'

    def ready(self):
        importlib.import_module('marketplace.signals')
