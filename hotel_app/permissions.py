from rest_framework.permissions import BasePermission


class IsGuest(BasePermission):
    """Allow only guests"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'guest'


class IsStaff(BasePermission):
    """Allow only staff"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'staff'


class IsOwnerOrStaff(BasePermission):
    """Allow staff or the owner of the resource"""
    def has_object_permission(self, request, view, obj):
        if request.user.profile.role == 'staff':
            return True
        return obj.user == request.user