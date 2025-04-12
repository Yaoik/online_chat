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

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f'{self.scope=}')
        
        user:User = self.scope["user"]
        self.user = user
        if self.user.is_anonymous:
            await self.close()
            return

        # Создаем уникальное имя группы для пользователя на основе его PK
        self.user_group_name = f"user_{self.user.pk}"
        
        # Добавляем канал пользователя в его группу
        self.channel_layer = cast(RedisChannelLayer, self.channel_layer)
        await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )

        await self.accept()

    async def disconnect(self, close_code):
        # При отключении удаляем пользователя из группы
        if not self.user.is_anonymous:
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data:str):
        # Обработка входящих сообщений от клиента (если нужно)
        try:
            text_data_json = json.loads(text_data)
        except Exception as e:
            await self.channel_layer.group_send(
                self.user_group_name,
                {
                    "type": "error",
                    "message": str(e),
                    "user": self.user.username,
                }
            )
            return
        
        message = text_data_json.get("message")

        if message:
            await self.channel_layer.group_send(
                self.user_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "user": self.user.username,
                }
            )
