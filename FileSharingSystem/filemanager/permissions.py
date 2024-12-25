from rest_framework.permissions import BasePermission

class IsOpsUser(BasePermission):
    def has_permission(self, request, view):
        # Ensure the user is authenticated and has the 'ops' user_type
        if request.user and request.user.is_authenticated and request.user.user_type == 'ops':
            return True
        return False
