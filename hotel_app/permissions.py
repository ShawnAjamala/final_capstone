from rest_framework.permissions import BasePermission

### ==================== ROLE-BASED PERMISSIONS ====================
# Run AFTER JWT authentication validates the token.
# Staff additionally checks is_approved — can register/login
# but cannot access staff endpoints until admin approves them.

class IsGuest(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'guest'
        )


class IsStaff(BasePermission):
    # Staff must be APPROVED by admin to pass this check
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'staff' and
            request.user.profile.is_approved
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'admin'
        )


class IsAdminOrStaff(BasePermission):
    # Admin always gets access, staff must be approved
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profile'):
            return False
        if request.user.profile.role == 'admin':
            return True
        if request.user.profile.role == 'staff' and request.user.profile.is_approved:
            return True
        return False

### ==================== END OF PERMISSIONS ====================