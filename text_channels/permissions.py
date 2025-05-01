from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from .models import Channel, ChannelBan, ChannelMembership


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


class CanManageBans(BasePermission):
    def has_permission(self, request: Request, view):
        channel_uuid = view.kwargs['channel_uuid']
        return ChannelMembership.objects.filter(
            user=request.user,
            channel__uuid=channel_uuid,
            is_admin=True,
        ).exists()

    def has_object_permission(self, request: Request, view, obj: ChannelBan):
        return ChannelMembership.objects.filter(
            user=request.user,
            channel=obj.channel,
            is_admin=True,
        ).exists()
