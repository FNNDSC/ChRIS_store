
from rest_framework import permissions


class IsOwnerOrChrisOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or superuser
    'chris' to modify/edit it. Read only is allowed to other users.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner and superuser 'chris'.
        return (request.user in obj.owner.all()) or (request.user.username == 'chris')


class IsStarOwnerOrChris(permissions.BasePermission):
    """
    Custom permission to only allow access to owners of plugin stars or superuser
    'chris'.
    """

    def has_object_permission(self, request, view, obj):
        # Access is only allowed to the owner and superuser 'chris'.
        return (request.user == obj.user) or (request.user.username == 'chris')


class IsMetaOwnerOrChrisOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an plugin's meta or superuser
    'chris' to modify/edit it. Read only is allowed to other users.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the obj's meta and
        # superuser 'chris'.
        user = request.user
        return (user in obj.meta.owner.all()) or (user.username == 'chris')
