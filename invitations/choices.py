from django.db import models


class ExpirationTimeChoices(models.TextChoices):
    ONE_HOUR = "1", "1 час"
    THREE_HOURS = "3", "3 часа"
    ONE_DAY = "24", "24 часа"
