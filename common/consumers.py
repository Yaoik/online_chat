import asyncio
import json
import logging
from typing import Generator, cast

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels_redis.core import RedisChannelLayer
from django.conf import settings
from redis.asyncio.client import Redis

from text_channels.models import ChannelMembership
from users.models import User

logger = logging.getLogger(__name__)


class MainConsumer(AsyncWebsocketConsumer):
    MAX_CONNECTIONS_PER_USER = settings.WEBSOCKET_MAX_CONNECTIONS_PER_USER
    TOO_MANY_CONNECTION_CODE = 4001
    REDIS_ERROR_CODE = 4003
    WEBSOCKET_LIVE_TIME = settings.WEBSOCKET_LIVE_TIME

    async def connect(self):
        self._is_connection_accepted = False  # Для обработки в self.disconnect()

        user: User = self.scope["user"]
        self.user = user
        if self.user.is_anonymous:
            logger.warning("Anonymous user attempted to connect")
            await self.close()
            return

        self.redis_key = f"websocket_user_{user.pk}"
        self.channel_layer: RedisChannelLayer = cast(RedisChannelLayer, get_channel_layer())

        try:
            self.redis: Redis = await self.channel_layer.connection(
                self.channel_layer.consistent_hash(self.redis_key)
            )
        except Exception as e:
            logger.critical(f'{e=}')
            await self.close(code=self.REDIS_ERROR_CODE)
            return

        current_connections = await self._get_current_connections()
        if current_connections is None:  # На случай если Redis упал
            await self.close(code=self.REDIS_ERROR_CODE)
            return
        elif current_connections >= self.MAX_CONNECTIONS_PER_USER:
            logger.warning(f"User {user.pk} has too many connections ({current_connections})")
            await self.close(code=self.TOO_MANY_CONNECTION_CODE, reason="Too many connections.")
            return

        self._is_connection_accepted = True

        await self._increment_connections()
        await self.channel_layer.group_add(self.redis_key, self.channel_name)

        await self._subscribe_to_user_channels()  # добавляем пользователя в группы websocket_channel_{channel.pk}

        await self.accept()

    async def disconnect(self, close_code: int):
        if not self.user.is_anonymous and self._is_connection_accepted:
            await self._decrement_connections()
            await self._unsubscribe_from_user_channels()  # удаляем пользователя из групп websocket_channel_{channel.pk}

    async def _subscribe_to_user_channels(self):
        """Подписывает пользователя на сообщения из его каналов."""
        groups = list(await self._get_channel_groups())
        results = await asyncio.gather(
            *[self.channel_layer.group_add(group, self.channel_name) for group in groups],
            return_exceptions=True
        )
        for group, result in zip(groups, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to subscribe to group {group}: {result}")

    async def _unsubscribe_from_user_channels(self):
        """Отписывает пользователя от сообщений из его каналов."""
        groups = list(await self._get_channel_groups())
        results = await asyncio.gather(
            *[self.channel_layer.group_discard(group, self.channel_name) for group in groups],
            return_exceptions=True
        )
        for group, result in zip(groups, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to unsubscribe to group {group}: {result}")

    async def _get_current_connections(self) -> int | None:
        """Возвращает текущее количество соединений пользователя."""
        if not self.redis:
            await self.close(code=self.REDIS_ERROR_CODE)
            return None

        try:
            result = await asyncio.wait_for(
                self.redis.get(self.redis_key),
                timeout=5.0
            )
            return int(result or 0)
        except asyncio.TimeoutError:
            logger.error(f"Redis operation timed out for key {self.redis_key}")
            await self.close(code=self.REDIS_ERROR_CODE)
            return None

    async def _increment_connections(self):
        """Увеличивает счётчик соединений."""
        if not self.redis:
            await self.close(code=self.REDIS_ERROR_CODE)
            return None

        await self.redis.incr(self.redis_key)
        await self.redis.expire(self.redis_key, self.WEBSOCKET_LIVE_TIME)  # что-бы избежать утечки памяти

    async def _decrement_connections(self):
        """Уменьшает счётчик соединений."""
        if not self.redis:
            await self.close(code=self.REDIS_ERROR_CODE)
            return None

        await self.redis.decr(self.redis_key)
        current_connections = await self._get_current_connections()
        if current_connections is not None and current_connections <= 0:
            await self.redis.delete(self.redis_key)
        elif current_connections is None:
            await self.close(code=self.REDIS_ERROR_CODE)

    async def _get_channel_groups(self) -> Generator[str, None, None]:
        channel_pks = await self.get_user_channels()
        return (f"websocket_channel_{pk}" for pk in channel_pks)

    @database_sync_to_async
    def get_user_channels(self) -> tuple[int]:
        return tuple(
            ChannelMembership.objects.filter(user=self.user)
            .values_list("channel__pk", flat=True)
        )

    async def chat_message(self, event: dict) -> None:
        """Метод для отправки MessageSerializer(Message).data всем пользователям в канале этого сообщения"""
        message_data = event["message"]
        channel_data = event["channel"]
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "data": {
                "message": message_data,
                "channel": channel_data,
            },
        }))

    async def unsubscribe_channel(self, event: dict) -> None:
        """
        Метод для отписки пользователя от группы канала.
        """
        channel_pk = event["channel_pk"]
        group_name = f"websocket_channel_{channel_pk}"
        try:
            await self.channel_layer.group_discard(group_name, self.channel_name)
        except Exception as e:
            logger.error(f"Failed to unsubscribe {self.user.username} from {group_name}: {e}")

    async def subscribe_channel(self, event: dict) -> None:
        """
        Метод для подписки пользователя на группу канала.
        """
        channel_pk = event["channel_pk"]
        group_name = f"websocket_channel_{channel_pk}"
        try:
            await self.channel_layer.group_add(group_name, self.channel_name)
        except Exception as e:
            logger.error(f"Failed to subscribe {self.user.username} from {group_name}: {e}")
