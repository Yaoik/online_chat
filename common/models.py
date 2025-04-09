from django.db import models

class BaseModel(models.Model):
    """Абстрактная модель на случай расширения"""

    class Meta:
        abstract = True
        
class Timestamped(BaseModel):
    """Абстрактная модель для меток времени создания/изменения"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True
