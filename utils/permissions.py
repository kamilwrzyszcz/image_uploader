from rest_framework import permissions

class IsAdminOrOwner(permissions.BasePermission):
    "Custom permission checking if user is admin or is owner of the resource."

    message = "Access only for owner or admin."

    def has_permission(self, request, view):
        return request.user.is_superuser or view.kwargs.get('user_id') == request.user.id

    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or obj.user == request.user


class TierHaveLinks(permissions.BasePermission):
    """Custom permission checking if user has link generation abilities."""

    message = "Tier of your account doesn't allow to generate links"

    def has_permission(self, request, view):
        return request.user.tier.can_generate_link
