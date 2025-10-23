"""Permission classes used by the quiz app API.

Currently provides a single permission that allows access only to the
creator/owner of a Quiz instance.
"""

from rest_framework import permissions


class IsCreator(permissions.BasePermission):
    """Allow access only to the object creator."""

    def has_object_permission(self, request, view, obj):
        return obj.creator == request.user