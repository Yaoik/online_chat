from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from text_channels.models import Channel, ChannelMembership

from .models import Message


class Permissionsss(BasePermission):
    def has_object_permission(self, request: Request, view, obj):
        return True

    def has_permission(self, request: Request, view):
        return True


class MessagePermissions(permissions.BasePermission):
    """
    Права доступа для операций с сообщениями:
    - GET (list/retrieve): только участники канала (не забаненные).
    - POST: только участники канала (не забаненные).
    - PATCH: только автор сообщения.
    - DELETE: только автор сообщения или администратор канала.
    """
    message = "You do not have permission to perform this action."

    def has_permission(self, request: Request, view) -> bool:
        channel = get_object_or_404(Channel, uuid=view.kwargs['channel_uuid'])
        is_member = ChannelMembership.objects.filter(
            user=request.user, channel=channel, is_baned=False
        ).exists()
        if not is_member:
            self.message = "You are not a member of this channel or you are banned."
            return False
        return True

    def has_object_permission(self, request: Request, view, obj: Message) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ('PATCH', 'PUT'):
            if obj.user != request.user:
                self.message = "You can only edit your own messages."
                return False
            return True

        if request.method == 'DELETE':
            is_author = obj.user == request.user
            is_admin = ChannelMembership.objects.filter(
                user=request.user, channel=obj.channel, is_baned=False, is_admin=True
            ).exists()
            if not (is_author or is_admin):
                self.message = "You can only delete your own messages or if you are a channel admin."
                return False
            return True

        return False
