import logging
import uuid
from typing import cast

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels_redis.core import RedisChannelLayer
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from invitations.models import Invitation

from .models import Channel, ChannelMembership
from .permissions import CanManageChannel, Permissionsss
from .serializers import (
    ChannelCreateSerializer,
    ChannelMembershipCreateSerializer,
    ChannelMembershipSerializer,
    ChannelSerializer,
)

logger = logging.getLogger(__name__)


class ChannelView(
    ModelViewSet,
):
    """
    Вьюшка для CRUD операций с каналами
    """
    permission_classes = [IsAuthenticated, CanManageChannel]
    pagination_class = None
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'uuid'
    lookup_url_kwarg = 'channel_uuid'

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ChannelCreateSerializer
        return ChannelSerializer

    def get_queryset(self):
        return Channel.objects.filter(memberships__user=self.request.user, memberships__is_baned=False).order_by('-id')

    def perform_create(self, serializer: ChannelCreateSerializer):
        user = self.request.user
        channel: Channel = serializer.save(owner=user)
        membership_serializer: ChannelMembershipCreateSerializer = ChannelMembershipCreateSerializer(data={})
        membership_serializer.is_valid(raise_exception=True)
        membership_serializer.save(
            user=user,
            channel=channel,
            is_admin=True
        )


class ChannelConnectView(
    GenericAPIView,
    mixins.CreateModelMixin,
):
    """
    POST запрос для подключения к каналу
    """
    serializer_class = ChannelMembershipCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses=ChannelSerializer,
    )
    def post(self, request: Request, invitation_uuid: uuid.UUID, *args, **kwargs):
        with transaction.atomic():
            invitation = get_object_or_404(
                Invitation,
                uuid=invitation_uuid,
                expires_in__gt=timezone.now(),
            )
            channel = invitation.channel

            if ChannelMembership.objects.filter(
                user=request.user,
                channel=channel,
            ).exists():
                return Response(
                    {"error": "Вы не можете подключиться в этот канал"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = cast(ChannelMembershipCreateSerializer, self.get_serializer(
                data=request.data, context={'invitation': invitation}))
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            data = ChannelSerializer(serializer.instance.channel).data
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer: ChannelMembershipCreateSerializer):
        invitation: Invitation = cast(Invitation, serializer.context['invitation'])
        serializer.save(
            user=self.request.user,
            channel=invitation.channel,
        )


class ChannelDisconnectView(
    GenericAPIView,
    mixins.DestroyModelMixin
):
    """
    DLETE запрос для отключения от канала
    """
    serializer_class = ChannelMembershipSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'channel__uuid'
    lookup_url_kwarg = 'channel_uuid'

    def get_queryset(self):
        return ChannelMembership.objects.filter(user=self.request.user, is_baned=False).select_related('user', 'channel')

    def delete(self, request: Request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance: ChannelMembership):
        instance.delete()
        self._ws(instance)

    def _ws(self, channel_membership: ChannelMembership) -> None:
        channel_layer = cast(RedisChannelLayer, get_channel_layer())
        if not channel_layer:
            logger.error("Channel layer is not configured")
            return

        group_name = f"websocket_user_{channel_membership.user.pk}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "unsubscribe_channel",
                "channel_pk": channel_membership.channel.pk
            }
        )
