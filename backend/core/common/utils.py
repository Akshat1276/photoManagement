from __future__ import annotations
from typing import Iterable
from django.contrib.auth import get_user_model

User = get_user_model()


def user_has_any_role(user: User, role_names: Iterable[str]) -> bool:
	"""
	Returns True if the user has any of the given roles (by name).
	"""
	if not user or not getattr(user, "is_authenticated", False):
		return False
	role_names = list(role_names)
	if not role_names:
		return False
	return user.roles.filter(name__in=role_names).exists()


def user_has_permission(user: User, permission_code: str) -> bool:
	"""
	Returns True if the user has the given permission code via any active role.
	Superusers and staff always return True.
	"""
	if not user or not getattr(user, "is_authenticated", False):
		return False
	if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
		return True
	from core.models import UserRoleMapping
	return UserRoleMapping.objects.filter(
		user=user,
		is_active=True,
		role__is_active=True,
		role__permissions__code=permission_code
	).exists()