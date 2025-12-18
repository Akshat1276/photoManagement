from rest_framework.permissions import SAFE_METHODS, BasePermission
from .utils import user_has_any_role


class IsOwnerOrReadOnly(BasePermission):
	def has_object_permission(self, request, view, obj):
		if request.method in SAFE_METHODS:
			return True
		user = request.user
		if not user or not user.is_authenticated:
			return False
		if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
			return True
		owner = None
		for attr in ("uploaded_by", "created_by", "user"):
			if hasattr(obj, attr):
				owner = getattr(obj, attr)
				break
		return owner == user
class HasAnyRole(BasePermission):
	required_roles: list[str] = []
	def has_permission(self, request, view):
		roles = getattr(view, "required_roles", self.required_roles)
		return user_has_any_role(request.user, roles)
class IsPhotographerOrAbove(HasAnyRole):
	required_roles = ["Photographer", "Event Coordinator", "IMG Member", "Admin"]
	def has_permission(self, request, view):
		user = request.user
		if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
			return True
		return super().has_permission(request, view)
class IsEventCoordinatorOrAbove(HasAnyRole):
	required_roles = ["Event Coordinator", "Admin"]
	def has_permission(self, request, view):
		user = request.user
		if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
			return True
		return super().has_permission(request, view)