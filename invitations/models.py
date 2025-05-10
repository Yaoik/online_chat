import uuid

from django.db import models
from django.utils import timezone

from common.models import Timestamped
from text_channels.models import Channel
from users.models import User

from .choices import ExpirationTimeChoices


class Invitation(Timestamped):
    """Приглашение в канал"""
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


class InvitationAcceptance(models.Model):
    """Модель для сохранения информации о том, какой пользователь использовал приглашение."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invitation_acceptances'
    )
    invitation = models.ForeignKey(
        Invitation,
        on_delete=models.CASCADE,
        related_name='acceptances'
    )
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['invitation', 'user'],
                name='unique_invitation_acceptance'
            )
        ]

    def __str__(self):
        return f"{self.user} accepted {self.invitation}"
