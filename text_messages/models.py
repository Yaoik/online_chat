import uuid

from django.db import models, transaction

from common.models import Timestamped
from users.models import User


class Message(Timestamped):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    channel = models.ForeignKey('text_channels.Channel', on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False, related_name='messages')
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    number = models.PositiveIntegerField(editable=False, default=0)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        unique_together = ('channel', 'number')
        ordering = ('-number', )

    def __str__(self):
        return f"{self.channel} -> <Message {self.pk}>"

    def save(self, *args, **kwargs):
        if not self.pk:
            with transaction.atomic():
                from text_channels.models import Channel
                channel = Channel.objects.select_for_update().get(pk=self.channel.pk)
                self.number = channel.last_message_number
                channel.last_message_number += 1
                channel.save(update_fields=('last_message_number', ))
        super().save(*args, **kwargs)
