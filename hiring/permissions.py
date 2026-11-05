from rest_framework import permissions


class IsDealParty(permissions.BasePermission):
    """
    Rule #8: Only the two parties of a Deal (the client or the worker)
    can view or perform actions on it.
    """

    message = "Only the client or worker of this deal can access it."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return (
            obj.client.user_id == user.id
            or obj.worker.client_profile.user_id == user.id
        )
