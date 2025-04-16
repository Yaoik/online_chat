import uuid
from typing import cast

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels_redis.core import RedisChannelLayer
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView

#from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

#from typing import Any, cast
from .models import Channel, ChannelMembership, Invitation, Message
from .permissions import (
    CanOperateInvitation,
    IsChannelAdmin,
    IsChannelMember,
    IsMessageAuthorOrChannelAdmin,
)
from .serializers import (  # ChannelMembershipCreateSerializer,
    ChannelCreateSerializer,
    ChannelMembershipSerializer,
    ChannelSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
)


class ChannelView(
    ModelViewSet,
):  
    """
    Вьюшка для CRUD операций с каналами
    """
    permission_classes = [IsAuthenticated, IsChannelAdmin]
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'uuid'
    lookup_url_kwarg = 'channel_uuid'
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ChannelCreateSerializer
        return ChannelSerializer

    def get_queryset(self):
        return Channel.objects.filter(memberships__user=self.request.user).order_by('-id')

    def perform_create(self, serializer:ChannelCreateSerializer):
        user = self.request.user
        channel = serializer.save(owner=user)
        ChannelMembership.objects.create(
            user=user,
            channel=channel,
            is_admin=True,
        )
    

class InvitationView(ModelViewSet):
    """
    Вьюшка для CRD приглашения
    """
    permission_classes = [IsAuthenticated, IsChannelAdmin, CanOperateInvitation]
    http_method_names = ['get', 'post', 'delete']
    lookup_field = 'uuid'
    lookup_url_kwarg = 'invitation_uuid'
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return InvitationCreateSerializer
        return InvitationSerializer
    
    def get_queryset(self):
        channel_uuid = self.kwargs['channel_uuid']
        return Invitation.objects.filter(channel__uuid=channel_uuid)
    
    def perform_create(self, serializer:ChannelCreateSerializer):
        user = self.request.user
        channel_uuid = self.kwargs['channel_uuid']
        channel = get_object_or_404(Channel, uuid=channel_uuid)
        serializer.save(channel=channel, author=user)
        
        
    
class ChannelConnectView(APIView):
    """
    Вьюшка для подключения к каналу по приглашению.
    GET: возвращает данные канала, если токен валидный.
    POST: подключает пользователя к каналу и возвращает данные канала.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return ChannelSerializer
    
    @extend_schema(
        request=None,
        responses=InvitationSerializer
    )
    def get(self, request:Request, invitation_uuid:uuid.UUID):
        """
        Возвращает данные канала по валидному токену приглашения.
        """
        invitation = get_object_or_404(
            Invitation,
            token=invitation_uuid,
            expires_in__gt=timezone.now(),
        )

        return Response(InvitationSerializer(invitation).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses=ChannelSerializer
    )
    def post(self, request:Request, invitation_uuid:uuid.UUID):
        """
        Подключает пользователя к каналу по токену приглашения.
        """
        invitation = get_object_or_404(
            Invitation,
            token=invitation_uuid,
            expires_in__gt=timezone.now(),
        )

        channel = invitation.channel
        
        if ChannelMembership.objects.filter(
            user=request.user,
            channel=channel
        ).exists():
            return Response(
                {"error": "Вы уже участник этого канала"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ChannelMembership.objects.create(
            user=request.user,
            channel=channel,
            is_admin=False
        )

        serializer = ChannelSerializer(channel)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MessageView(
    ModelViewSet,
):
    """
    Вьюшка для всех CRUD операций с сообщениями
    """
    permission_classes = [IsAuthenticated, IsChannelMember, IsMessageAuthorOrChannelAdmin]
    serializer_class = MessageSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'uuid'
    lookup_url_kwarg = 'message_uuid'
    
    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        channel_uuid = self.kwargs['channel_uuid']
        return Message.objects.filter(channel__uuid=channel_uuid).order_by('-id')

    def perform_create(self, serializer:MessageCreateSerializer):
        channel_uuid = self.kwargs['channel_uuid']
        channel = get_object_or_404(Channel, uuid=channel_uuid)
        user = self.request.user
        message = serializer.save(channel=channel, user=user)
        self._send_ws_message(message)
    
    def _send_ws_message(self, message: Message) -> None:
        channel_layer = cast(RedisChannelLayer, get_channel_layer())
        message_data = MessageSerializer(message).data
        
        async_to_sync(channel_layer.group_send)(
            f"channel_{message.channel.pk}",
            {
                "type": "chat.message",
                "message": message_data,
            }
        )

class ChannelMembershipView(
    GenericAPIView,
    mixins.DestroyModelMixin,
):
    serializer_class = ChannelMembershipSerializer
    permission_classes = [IsAuthenticated, IsChannelMember]
    
    def get_queryset(self):
        return ChannelMembership.objects.filter(user=self.request.user).order_by('-id')
    
    def delete(self, request:Request, *args, **kwargs):
        pass