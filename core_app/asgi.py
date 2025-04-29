import logging
import os
from functools import partial
from urllib.parse import parse_qs

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_app.settings')

django.setup()

# fmt: off

from channels.auth import AuthMiddlewareStack
from channels.middleware import BaseMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import CookieMiddleware
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.asgi import get_asgi_application
from django.db import close_old_connections
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from common.urls import websocket_urlpatterns
from users.models import User

# fmt: on

logger = logging.getLogger(__name__)


def validate_token(token: str | None) -> AccessToken | None:
    try:
        access_token = AccessToken(token)  # type: ignore
        return access_token
    except (InvalidToken, TokenError) as e:
        return None


async def get_user(validated_token: AccessToken):
    try:
        user: User = await User.objects.aget(id=validated_token["user_id"])
        return user
    except User.DoesNotExist:
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner: CookieMiddleware):
        self.inner = inner

    async def __call__(self, scope: dict, receive, send: partial):
        close_old_connections()

        scope["user"] = AnonymousUser()

        token = None

        query_string = scope.get("query_string", b"").decode("utf-8")
        if query_string:
            query_params = parse_qs(query_string)
            token = query_params.get("token", [None])[0]

        token = validate_token(token=token)

        if token is not None:
            if token.get('for_websocket', None):
                scope["user"] = await get_user(token)

        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JwtAuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
