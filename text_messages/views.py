import logging
from typing import cast

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels_redis.core import RedisChannelLayer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from text_channels.models import Channel
from text_channels.serializers import WebsocketChannelSerializer

from .models import Message
from .permissions import MessagePermissions
from .serializers import MessageCreateSerializer, MessageSerializer

logger = logging.getLogger(__name__)


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
        return Message.objects.filter(channel__uuid=channel_uuid)

    def perform_create(self, serializer: MessageCreateSerializer):
        channel_uuid = self.kwargs['channel_uuid']
        channel = get_object_or_404(Channel, uuid=channel_uuid)
        user = self.request.user
        message = serializer.save(channel=channel, user=user)
        self._send_ws_message(message)

    def _send_ws_message(self, message: Message) -> None:
        channel_layer = cast(RedisChannelLayer, get_channel_layer())
        if not channel_layer:
            logger.error("Channel layer is not configured")
            return

        serialized_message = MessageSerializer(message).data
        serialized_channel = WebsocketChannelSerializer(message).data
        group_name = f"websocket_channel_{message.channel.pk}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "chat_message",
                "message": serialized_message,
                "channel": serialized_channel,
            }
        )
