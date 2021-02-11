import operator

import rules
from rules.predicates import is_authenticated

from marketplace.domain import marketplace


rules.add_perm('user.is_same_user', operator.eq)

rules.add_perm('user.is_authenticated', is_authenticated)

rules.add_rule('user.is_site_staff', marketplace.user.is_site_staff)

rules.add_rule('volunteer.new_user_review', marketplace.user.is_site_staff)
