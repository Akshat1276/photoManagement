from __future__ import annotations
from typing import Iterable
from django.contrib.auth import get_user_model

User = get_user_model()

def user_has_any_role(user: User, role_names: Iterable[str]) -> bool:
	if not user or not getattr(user, "is_authenticated", False):
		return False
	from core.models import UserRole
	role_names = list(role_names)
	if not role_names:
		return False
	return UserRole.objects.filter(user=user, role__name__in=role_names).exists()