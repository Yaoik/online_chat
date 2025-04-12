from django.db import models
from common.models import Timestamped
import uuid
from users.models import User
from django.utils import timezone
from .choices import ExpirationTime

class Channel(Timestamped):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False, related_name='my_channels')
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

class Message(Timestamped):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        
    def __str__(self):
        return f"{self.channel} -> <Message {self.pk}>"
    
class Invitation(Timestamped):
    token = models.UUIDField(default=uuid.uuid4(), primary_key=True, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='invitations')
    expires_in = models.DateTimeField(editable=False)
    expiration_period = models.CharField(
        max_length=2,
        choices=ExpirationTime.choices,
        default=ExpirationTime.ONE_HOUR
    )
    
    class Meta:
        verbose_name = "Пригланешие"
        verbose_name_plural = "Приглашения"
        indexes = [
            models.Index(fields=['token', 'channel']),
        ]
        
    def __str__(self):
        return f"<Invitation {self.pk}>"
    
    @property
    def is_expired(self) -> bool:
        return self.expires_in <= timezone.now()
    
    def save(self, *args, **kwargs):
        if not self.expires_in:
            hours = int(self.expiration_period)
            self.expires_in = timezone.now() + timezone.timedelta(hours=hours)
        super().save(*args, **kwargs)