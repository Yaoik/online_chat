from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from .models import ChannelMembership, Message
from rest_framework.request import Request
from chat.models import Channel
from typing import cast



class CanOperateInvitation(BasePermission):
    def has_object_permission(self, request:Request, view, obj:Channel):
        return ChannelMembership.objects.filter(            
            user=request.user,
            channel=obj,
            is_admin=True,
            ).exists()
    def has_permission(self, request: Request, view):
        channel_uuid = view.kwargs.get('channel_uuid')
        if not channel_uuid:
            raise PermissionDenied('Channel UUID is required')
        if not ChannelMembership.objects.filter(
            user=request.user,
            channel__uuid=channel_uuid,
            is_admin=True,
        ).exists():
            raise PermissionDenied('Only channel admins can perform this action')
        return True
    
class IsChannelMember(BasePermission):
    def has_permission(self, request, view):
        channel_uuid = view.kwargs.get('channel_uuid')  # Используем channel_uuid
        if not channel_uuid:
            return True  # Для операций без channel_uuid (например, список каналов)
        if not ChannelMembership.objects.filter(
            user=request.user,
            channel__uuid=channel_uuid  # Проверяем по uuid канала
        ).exists():
            raise PermissionDenied('User is not a member of this channel')
        return True

class IsChannelAdmin(BasePermission):
    def has_permission(self, request, view):
        channel_id = view.kwargs.get('channel_id') or view.kwargs.get('pk')
        if not channel_id:
            return True
        if not ChannelMembership.objects.filter(
            user=request.user,
            channel_id=channel_id,
            is_admin=True
        ).exists():
            raise PermissionDenied('Only channel admins can perform this action')
        return True

class IsMessageAuthorOrChannelAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Message):
            return True
        if obj.user == request.user:
            return True
        if ChannelMembership.objects.filter(
            user=request.user,
            channel=obj.channel,
            is_admin=True
        ).exists():
            return True
        raise PermissionDenied('Only message author or channel admin can perform this action')