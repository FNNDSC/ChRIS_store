
from rest_framework import permissions


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to modify/edit it.
    Read only is allowed to other users.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the authenticated user
        return obj == request.user


class IsUser(permissions.BasePermission):
    """
    Custom permission to only allow access to the user that owns the object.
    """

    def has_object_permission(self, request, view, obj):
        # Access is only allowed to the owner
        return request.user == obj
