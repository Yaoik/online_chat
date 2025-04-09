from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from common.models import Timestamped
from .managers import CustomUserManager

class User(AbstractBaseUser, Timestamped, PermissionsMixin):
    """Основная модель пользователя"""
    
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()
    
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        constraints = [
            models.UniqueConstraint(
                Lower("username"), name="unique_username_case_insensitive"
            ),
        ]

    def __str__(self):
        return f'<User {self.username}>'