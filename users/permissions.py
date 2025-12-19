from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Check if object has owner attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # For User model
        if obj == request.user:
            return True

        return False


class IsModerator(permissions.BasePermission):
    """
    Custom permission to only allow moderators.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if user is in 'moderators' group
        return request.user.groups.filter(name='moderators').exists()

    def has_object_permission(self, request, view, obj):
        # Moderators have permission for all objects
        return self.has_permission(request, view)


class IsOwnerOrModerator(permissions.BasePermission):
    """
    Custom permission to allow owners or moderators.
    """

    def has_permission(self, request, view):
        # Both owners and moderators need to be authenticated
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Moderators can do anything
        if request.user.groups.filter(name='moderators').exists():
            return True

        # Check if object has owner attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # For User model
        if obj == request.user:
            return True

        return False


class IsNotModerator(permissions.BasePermission):
    """
    Custom permission to deny moderators.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return not request.user.groups.filter(name='moderators').exists()

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class CanCreateObject(permissions.BasePermission):
    """
    Custom permission to allow creation only for non-moderators.
    """

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True

        if not request.user.is_authenticated:
            return False

        return not request.user.groups.filter(name='moderators').exists()


class CanDeleteObject(permissions.BasePermission):
    """
    Custom permission to allow deletion only for owners (not moderators).
    """

    def has_object_permission(self, request, view, obj):
        if request.method != 'DELETE':
            return True

        if not request.user.is_authenticated:
            return False

        # Moderators cannot delete
        if request.user.groups.filter(name='moderators').exists():
            return False

        # Check if object has owner attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        return False