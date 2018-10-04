from namespaces import Namespace

from .user import UserDomain


marketplace = MarketplaceDomain = Namespace('marketplace')

MarketplaceDomain._add_(UserDomain)
