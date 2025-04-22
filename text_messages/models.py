import uuid

from django.db import models

from common.models import Timestamped
from users.models import User


class Message(Timestamped):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    channel = models.ForeignKey('text_channels.Channel', on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False, related_name='messages')
    content = models.TextField()

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self):
        return f"{self.channel} -> <Message {self.pk}>"
