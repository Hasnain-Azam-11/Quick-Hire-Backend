from rest_framework import permissions

from worker.models import WorkerBio


class IsWorkerBioOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.client_profile.user == request.user



class IsWorkerServiceOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.worker.client_profile.user == request.user


