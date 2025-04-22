import uuid
from typing import cast

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels_redis.core import RedisChannelLayer
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView

# from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from text_channels.models import Channel

from .models import Message
from .permissions import MessagePermissions, Permissionsss
from .serializers import MessageCreateSerializer, MessageSerializer


class MessageView(
    ModelViewSet,
):
    """
    Вьюшка для всех CRUD операций с сообщениями
    """
    permission_classes = (IsAuthenticated, MessagePermissions)
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
        return Message.objects.filter(channel__uuid=channel_uuid).order_by('-created_at')

    def perform_create(self, serializer: MessageCreateSerializer):
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
