
from rest_framework import permissions


class IsUserOrChrisOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or superuser
    'chris' to modify/edit it. Read only is allowed to other users.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the authenticated user and
        # superuser 'chris'.
        return (obj == request.user) or (request.user.username == 'chris')


class IsUserOrChris(permissions.BasePermission):
    """
    Custom permission to only allow access to the user that owns the object or
    superuser 'chris'.
    """

    def has_object_permission(self, request, view, obj):
        # Access is only allowed to the owner and superuser 'chris'.
        return (request.user == obj) or (request.user.username == 'chris')