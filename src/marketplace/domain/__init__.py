from namespaces import Namespace

from .notifications import NotificationDomain
from .user import UserDomain
from .proj import ProjectDomain


marketplace = MarketplaceDomain = Namespace('marketplace')

MarketplaceDomain._add_(NotificationDomain)
MarketplaceDomain._add_(UserDomain)
MarketplaceDomain._add_(ProjectDomain)
