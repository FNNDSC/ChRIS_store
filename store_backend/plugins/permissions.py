from rest_framework import permissions
from .models import PluginMetaCollaborator


class IsMetaOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the collaborators with owner role to modify/edit a
    plugin meta. Read-only is allowed to all other users.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owners.
        try:
            collab = PluginMetaCollaborator.objects.get(meta=obj, user=request.user)
        except PluginMetaCollaborator.DoesNotExist:
            return False
        return collab.role == 'O'


class IsStarOwner(permissions.BasePermission):
    """
    Custom permission to only allow access to the owner of a plugin star.
    """

    def has_object_permission(self, request, view, obj):
        # Access is only allowed to the owner.
        return request.user == obj.user


class IsMetaOwnerOrCollabReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow write access to the owners of a plugin meta.
    Read-only is allowed to all collaborators.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are only allowed to the collaborators.
        try:
            collab = PluginMetaCollaborator.objects.get(meta=obj, user=request.user)
        except PluginMetaCollaborator.DoesNotExist:
            return False
        return request.method in permissions.SAFE_METHODS or collab.role == 'O'


class IsObjMetaOwnerAndNotUserOrCollabReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the owners of an obj's meta to modify/edit and only
    when the request user is not the owner of the obj. Read-only is allowed to all
    collaborators.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are only allowed to the collaborators.
        try:
            collab = PluginMetaCollaborator.objects.get(meta=obj.meta, user=request.user)
        except PluginMetaCollaborator.DoesNotExist:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return collab.role == 'O' and obj.user != request.user


class IsObjMetaOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the owners of an obj's meta to write it.
    Read-only is allowed to all other users.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        try:
            collab = PluginMetaCollaborator.objects.get(meta=obj.meta, user=request.user)
        except PluginMetaCollaborator.DoesNotExist:
            return False
        return collab.role == 'O'
