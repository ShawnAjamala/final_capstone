import os
from rest_framework.permissions import BasePermission
from .models import UserProfile


def get_user_profile(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return None


### ==================== ROLE-BASED PERMISSIONS ====================
# Run AFTER JWT authentication validates the token.
# Staff additionally checks is_approved — can register/login
# but cannot access staff endpoints until admin approves them.

class IsGuest(BasePermission):
    def has_permission(self, request, view):
        profile = get_user_profile(request.user)
        return (
            request.user.is_authenticated and
            profile is not None and
            profile.role == 'guest'
        )


class IsStaff(BasePermission):
    # Staff must be APPROVED by admin to pass this check
    def has_permission(self, request, view):
        profile = get_user_profile(request.user)
        return (
            request.user.is_authenticated and
            profile is not None and
            profile.role == 'staff' and
            profile.is_approved
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        profile = get_user_profile(request.user)
        return (
            request.user.is_authenticated and
            profile is not None and
            profile.role == 'admin'
        )


class IsAdminOrStaff(BasePermission):
    # Admin always gets access, staff must be approved
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        profile = get_user_profile(request.user)
        if profile is None:
            return False
        if profile.role == 'admin':
            return True
        if profile.role == 'staff' and profile.is_approved:
            return True
        return False


class AdminBootstrapPermission(BasePermission):
    """Restrict the one-time admin bootstrap to a secret value."""

    def has_permission(self, request, view):
        secret = os.getenv('BOOTSTRAP_ADMIN_SECRET', '').strip()
        if not secret:
            return False

        provided = (
            request.headers.get('X-Admin-Bootstrap-Key')
            or request.headers.get('X-Admin-Bootstrap-Secret')
            or request.GET.get('bootstrap_secret')
        )

        if hasattr(request, 'data') and isinstance(request.data, dict):
            provided = provided or request.data.get('bootstrap_secret')

        return provided == secret

### ==================== END OF PERMISSIONS ====================