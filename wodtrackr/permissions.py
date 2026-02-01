from rest_framework.permissions import BasePermission, SAFE_METHODS


class ExercisePermission(BasePermission):
    """
    Role-based permissions for Exercise endpoints.

    - Auth required for all endpoints.
    - Admins can manage any exercise.
    - Non-admins can manage only their own exercises.
    - Read access allowed for public exercises or owned exercises.
    """

    def _role(self, user):
        profile = getattr(user, 'profile', None)
        if profile and getattr(profile, 'role', None):
            return profile.role
        return 'user'

    def _is_admin(self, user):
        return user.is_staff or self._role(user) == 'admin'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if self._is_admin(request.user):
            return True

        if request.method in SAFE_METHODS:
            return obj.is_public or obj.created_by == request.user

        return obj.created_by == request.user
