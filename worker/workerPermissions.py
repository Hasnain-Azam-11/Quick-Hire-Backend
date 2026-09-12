from rest_framework import permissions

from worker.models import WorkerBio


class IsWorkerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.client_profile.user == request.user
