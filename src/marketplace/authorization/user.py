from rules import add_perm, predicate
from rules.predicates import is_authenticated

from marketplace.models.user import User
from marketplace.domain.user import UserService


add_perm('user.is_authenticated', is_authenticated)

@predicate
def is_same_user(request_user, target_user):
    return request_user == target_user

add_perm('user.is_same_user', is_same_user)

add_perm('volunteer.new_user_review', UserService.user_is_dssg_staff)
