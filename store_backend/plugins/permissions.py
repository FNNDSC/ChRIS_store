from rest_framework import permissions
from .models import PluginMetaCollaborator


class IsStarOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow write access to the owner of a plugin star.
    Read-only is allowed to all other users.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write access is only allowed to the owner.
        return request.user == obj.user


class IsMetaOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the collaborators with owner role to write a
    plugin meta. Read-only is allowed to all other users.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owners.
        if request.user.is_authenticated:
            try:
                collab = PluginMetaCollaborator.objects.get(meta=obj, user=request.user)
            except PluginMetaCollaborator.DoesNotExist:
                return False  # not even a collaborator
            return collab.role == 'O'
        return False


class IsObjMetaOwnerAndNotUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow write access to the owners of an obj's meta and only
    when the request user is not the owner of the obj. Read-only is allowed to all other
    users.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Read permissions are only allowed to the collaborators.
        if request.user.is_authenticated:
            try:
                collab = PluginMetaCollaborator.objects.get(meta=obj.meta,
                                                            user=request.user)
            except PluginMetaCollaborator.DoesNotExist:
                return False  # not even a collaborator
            return collab.role == 'O' and obj.user != request.user
        return False


class IsObjMetaOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow write access to the owners of an obj's meta.
    Read-only is allowed to all other users.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_authenticated:
            try:
                collab = PluginMetaCollaborator.objects.get(meta=obj.meta,
                                                            user=request.user)
            except PluginMetaCollaborator.DoesNotExist:
                return False
            return collab.role == 'O'
        return False
