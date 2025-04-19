from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from .models import Channel, ChannelMembership


class Permissionsss(BasePermission):
    def has_object_permission(self, request: Request, view, obj):
        return True

    def has_permission(self, request: Request, view):
        return True


class CanManageChannel(BasePermission):
    def has_object_permission(self, request: Request, view, obj: Channel):
        if request.method == 'GET':
            return True

        if request.method in ('PUT', 'PATCH'):
            return (
                obj.owner == request.user or
                ChannelMembership.objects.filter(
                    user=request.user,
                    channel=obj,
                    is_admin=True,
                ).exists()
            )
        if request.method in ('DELETE',):
            return obj.owner == request.user

        return False
