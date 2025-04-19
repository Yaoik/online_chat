import uuid

from django.db import models

from common.models import Timestamped
from users.models import User


class Channel(Timestamped):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False, related_name='user_channels')
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Канал"
        verbose_name_plural = "Каналы"

    def __str__(self):
        return f"<Channel {self.pk}>"


class ChannelMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channels')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='memberships')
    is_admin = models.BooleanField(default=False, verbose_name="Администратор")
    is_baned = models.BooleanField(default=False, verbose_name="Забанен")

    class Meta:
        verbose_name = "Членство в канале"
        verbose_name_plural = "Членства в каналах"
        constraints = (
            models.UniqueConstraint(fields=['user', 'channel'], name='user_channel_unique_together'),
        )
        indexes = [
            models.Index(fields=["user", "channel"]),
        ]

    def __str__(self):
        return f"{self.user} в {self.channel} (admin: {self.is_admin})"
