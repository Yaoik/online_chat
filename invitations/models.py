import uuid

from django.db import models
from django.utils import timezone

from common.models import Timestamped
from text_channels.models import Channel
from users.models import User

from .choices import ExpirationTimeChoices


class Invitation(Timestamped):
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='invitations')
    expires_in = models.DateTimeField(editable=False)
    expiration_period = models.CharField(
        max_length=2,
        choices=ExpirationTimeChoices.choices,
        default=ExpirationTimeChoices.ONE_HOUR
    )

    class Meta:
        verbose_name = "Пригланешие"
        verbose_name_plural = "Приглашения"
        indexes = [
            models.Index(fields=['uuid', 'channel']),
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
