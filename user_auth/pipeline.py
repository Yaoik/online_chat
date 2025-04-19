from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.utils.functional import SimpleLazyObject
from social_django.strategy import DjangoStrategy

from users.models import User

from .utils import CustomRefreshToken


def check_existing_user(backend: DjangoStrategy, details: dict, user: None | SimpleLazyObject = None, *args: tuple, **kwargs: dict):
    """
    Проверяет, существует ли пользователь с email, полученным от Provider.
    Если пользователь существует, возвращает его, иначе продолжает pipeline.
    """
    email = details.get('email')
    if email:
        users: QuerySet[User] = User.objects.filter(email=email)
        if users.exists():
            return {'user': users.first(), 'is_new': False}
    return {}


def add_ntoken_redirect(backend: DjangoStrategy, details: dict, user: None | SimpleLazyObject = None, *args: tuple, **kwargs: dict):
    if user:
        refresh_token = CustomRefreshToken.for_user_with_lifetime(user, lifetime=timedelta(seconds=60))
        redirect_url = kwargs.get('redirect_url', settings.SOCIAL_AUTH_REDIRECT_URI)
        params = urlencode({'refresh_token': refresh_token})
        redirect_url = f"{redirect_url}?{params}"
        return redirect(redirect_url)
