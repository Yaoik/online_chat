import uuid

from django.db import models

from common.models import Timestamped
from users.models import User


class Channel(Timestamped):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False, related_name='user_channels')
    last_message_number = models.PositiveIntegerField(default=0, editable=False)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Канал"
        verbose_name_plural = "Каналы"
        constraints = [
            models.UniqueConstraint(fields=['name', 'owner'], name='unique_channel_name_per_owner'),
        ]

    def __str__(self):
        return f"<Channel {self.pk}>"


class ChannelMembership(Timestamped):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channels')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='memberships')
    is_admin = models.BooleanField(default=False, verbose_name="Администратор")

    class Meta:
        verbose_name = "Членство в канале"
        verbose_name_plural = "Членства в каналах"
        constraints = (
            models.UniqueConstraint(fields=['user', 'channel'], name='membership_user_channel_unique_together'),
        )
        indexes = [
            models.Index(fields=["user", "channel"]),
        ]

    def __str__(self):
        return f"{self.user} в {self.channel} (admin: {self.is_admin})"


class ChannelBan(Timestamped):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='bans_info'
    )
    banned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='bans_given'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bans'
    )
    reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Бан в канале"
        verbose_name_plural = "Баны в каналах"
        constraints = (
            models.UniqueConstraint(fields=['user', 'channel'], name='ban_user_channel_unique_together'),
        )
        indexes = [
            models.Index(fields=["user", "channel"]),
        ]

    def __str__(self):
        return f"<ChannelBan in {self.channel} for {self.user}>"
