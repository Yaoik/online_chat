import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message
from users.models import User
from .serializers import MessageSerializer
from typing import cast
from channels_redis.core import RedisChannelLayer
import uuid
import logging
from chat.models import ChannelMembership

logger = logging.getLogger(__name__)



class MainConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f"Connecting WebSocket for user: {self.scope['user']}")
        
        user: User = self.scope["user"]
        self.user = user
        if self.user.is_anonymous:
            logger.warning("Anonymous user attempted to connect")
            await self.close()
            return

        self.channel_groups = await self.get_user_channels()
        
        self.channel_layer = cast(RedisChannelLayer, self.channel_layer)
        for channel_id in self.channel_groups:
            group_name = f"channel_{channel_id}"
            await self.channel_layer.group_add(group_name, self.channel_name)
            logger.info(f"Added user {self.user.username} to group {group_name}")

        await self.accept()
        logger.info(f"WebSocket connected for user {self.user.username}")

    async def disconnect(self, close_code):
        if not self.user.is_anonymous:
            # Удаляем пользователя из всех групп каналов
            for channel_id in self.channel_groups:
                group_name = f"channel_{channel_id}"
                await self.channel_layer.group_discard(group_name, self.channel_name)
                logger.info(f"Removed user {self.user.username} from group {group_name}")
        logger.info(f"WebSocket disconnected for user {self.user.username}")

    async def receive(self, text_data: str):
        return None

    async def chat_message(self, event):
        message_data = event["message"]
        logger.info(f"Sending message to {self.user.username}: {message_data}")
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message_data,
        }))

    @database_sync_to_async
    def get_user_channels(self):
        # Получаем ID всех каналов, в которых состоит пользователь
        return list(
            ChannelMembership.objects.filter(user=self.user)
            .values_list("channel__id", flat=True)
        )