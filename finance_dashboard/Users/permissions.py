"""
Custom DRF permission classes that enforce role-based access control.

Usage in views:
    permission_classes = [IsAuthenticated, IsAdmin]
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    permission_classes = [IsAuthenticated, IsActiveUser]
"""

from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    """Rejects inactive/suspended accounts even if they hold a valid JWT."""
    message = "Your account has been deactivated. Contact an administrator."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsAdmin(BasePermission):
    """Only Admin role."""
    message = "This action requires Admin privileges."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_admin
        )


class IsAnalystOrAbove(BasePermission):
    """Analyst or Admin role."""
    message = "This action requires Analyst or Admin privileges."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_analyst  # True for analyst + admin
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Allows safe methods (GET, HEAD, OPTIONS) for any authenticated user,
    but restricts write methods to Admin only.
    Useful for endpoints where viewers/analysts should see data but not mutate it.
    """
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
    message = "Write operations require Admin privileges."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        if request.method in self.SAFE_METHODS:
            return True
        return request.user.is_admin