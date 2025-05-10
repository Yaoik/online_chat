import logging
import uuid
from typing import cast

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels_redis.core import RedisChannelLayer
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from invitations.models import Invitation, InvitationAcceptance
from text_channels.models import ChannelBan
from users.models import User

from .models import Channel, ChannelMembership
from .permissions import CanManageBans, CanManageChannel
from .serializers import (ChannelBanSerializer, ChannelCreateSerializer,
                          ChannelMembershipCreateSerializer,
                          ChannelMembershipSerializer, ChannelSerializer)

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
        return Channel.objects.filter(memberships__user=self.request.user).exclude(bans_info__user=self.request.user).order_by('-id')

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
                    {"error": "Вы уже в этом канале"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if ChannelBan.objects.filter(
                user=request.user,
                channel=channel,
            ).exists():
                return Response(
                    {"error": "Вы забанены в этом канале"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = cast(ChannelMembershipCreateSerializer, self.get_serializer(
                data=request.data, context={'invitation': invitation}))
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            self._ws(channel=channel, user=request.user)  # добавляем в группу вебсокетов
            headers = self.get_success_headers(serializer.data)
            data = ChannelSerializer(serializer.instance.channel).data
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer: ChannelMembershipCreateSerializer):
        invitation: Invitation = cast(Invitation, serializer.context['invitation'])
        with transaction.atomic():
            serializer.save(
                user=self.request.user,
                channel=invitation.channel,
            )
            InvitationAcceptance.objects.get_or_create(
                user=self.request.user,
                invitation=invitation,
            )

    def _ws(self, channel: Channel, user: User) -> None:
        """
        При подключении пользователя добавляем его в группу вебсокета
        """
        channel_layer = cast(RedisChannelLayer, get_channel_layer())
        if not channel_layer:
            logger.error("Channel layer is not configured")
            return

        group_name = f"websocket_user_{user.pk}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "subscribe_channel",
                "channel_pk": channel.pk
            }
        )


class ChannelDisconnectView(
    GenericAPIView,
    mixins.DestroyModelMixin
):
    """
    DELETE запрос для отключения от канала
    """
    serializer_class = ChannelMembershipSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'channel__uuid'
    lookup_url_kwarg = 'channel_uuid'

    def get_queryset(self):
        return ChannelMembership.objects.filter(user=self.request.user)

    def delete(self, request: Request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance: ChannelMembership):
        instance.delete()
        self._ws(instance)

    def _ws(self, channel_membership: ChannelMembership) -> None:
        """
        При отключении пользователя удаляем его из группы вебсокета
        """
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


class ChannelBanListView(
    GenericAPIView,
    mixins.ListModelMixin,
):
    """
    R операции с банами
    """
    serializer_class = ChannelBanSerializer
    permission_classes = [IsAuthenticated, CanManageBans]

    def get_queryset(self):
        return ChannelBan.objects.filter(channel__uuid=self.kwargs['channel_uuid'])

    def get(self, request, channel_uuid: uuid.UUID, *args, **kwargs):
        return super().list(request, channel_uuid=channel_uuid, *args, **kwargs)


class ChannelCreateDeleteBanView(
    GenericAPIView,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
):
    """
    CD операции с банами
    """
    serializer_class = ChannelBanSerializer
    permission_classes = [IsAuthenticated, CanManageBans]
    lookup_field = 'user__id'
    lookup_url_kwarg = 'user_id'

    def get_queryset(self):
        return ChannelBan.objects.filter(channel__uuid=self.kwargs['channel_uuid'])

    def perform_create(self, serializer: ChannelBanSerializer):
        channel = get_object_or_404(Channel, uuid=self.kwargs['channel_uuid'])
        banned_by = self.request.user
        user = get_object_or_404(User, id=self.kwargs.get('user_id'))

        if user.pk == banned_by.pk:
            raise ValidationError("Нельза забанить себя.")

        user_channel_membership = ChannelMembership.objects.filter(
            user=user,
            channel=channel,
            is_admin=False,
        ).first()
        if not user_channel_membership:
            raise ValidationError("Пользователь не в канале или админ.")

        serializer.save(
            channel=channel,
            user=user,
            banned_by=banned_by,
        )
        user_channel_membership.delete()

    def post(self, request, channel_uuid: uuid.UUID, user_id: int, *args, **kwargs):
        return super().create(request, channel_uuid=channel_uuid, user_id=user_id, *args, **kwargs)

    def delete(self, request, channel_uuid: uuid.UUID, user_id: int, *args, **kwargs):
        return self.destroy(request, channel_uuid=channel_uuid, user_id=user_id, *args, **kwargs)
