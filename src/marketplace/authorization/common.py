import rules
from django.core.exceptions import PermissionDenied


def ensure_rule(rule, *args):
    if not rules.test_rule(rule, *args):
        raise PermissionDenied


def ensure_user_has_permission(user, target, permission):
    if not user.has_perm(permission, target):
        raise PermissionDenied
