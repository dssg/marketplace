from namespaces import Namespace

from .notifications import NotificationDomain
from .user import UserDomain


marketplace = MarketplaceDomain = Namespace('marketplace')

MarketplaceDomain._add_(NotificationDomain)
MarketplaceDomain._add_(UserDomain)
