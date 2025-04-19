from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.request import Request

from text_channels.models import Channel, ChannelMembership


class InvitationPermissions(permissions.BasePermission):
    """
    Права доступа для операций с приглашениями:
    - POST: только администраторы канала.
    - DELETE: только администраторы канала.
    - GET (list): только администраторы канала.
    - GET (retrieve): все аутентифицированные пользователи.
    """
    message = "You do not have permission to perform this action."

    def has_permission(self, request: Request, view) -> bool:
        if not request.user.is_authenticated:
            self.message = "Authentication required."
            return False

        channel_uuid = view.kwargs.get('channel_uuid')
        channel = get_object_or_404(Channel, uuid=channel_uuid)

        if view.action == 'retrieve':
            return True

        is_admin = ChannelMembership.objects.filter(
            user=request.user, channel=channel, is_baned=False, is_admin=True
        ).exists()
        if not is_admin:
            self.message = "Only channel admins can perform this action."
            return False
        return True

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if view.action == 'retrieve':
            return True

        if view.action == 'destroy':
            is_admin = ChannelMembership.objects.filter(
                user=request.user, channel=obj.channel, is_baned=False, is_admin=True
            ).exists()
            if not is_admin:
                self.message = "Only channel admins can delete invitations."
                return False
            return True

        return False
