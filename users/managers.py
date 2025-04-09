from django.contrib.auth.models import UserManager


class CustomUserManager(UserManager):
    """Менеджер для кастомной модели пользователя"""

