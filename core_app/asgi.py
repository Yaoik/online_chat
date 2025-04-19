import logging
import os
from urllib.parse import parse_qs

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_app.settings')

django.setup()

# fmt: off
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.asgi import get_asgi_application
from django.db import close_old_connections
from jwt import decode as jwt_decode
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from common.urls import websocket_urlpatterns
from users.models import User

# fmt: on

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user(validated_token):
    try:
        user = get_user_model().objects.get(id=validated_token["user_id"])
        return user
    except User.DoesNotExist:
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()

        token = None
        for header in scope["headers"]:
            if header[0].decode("utf-8").lower() == "authorization":
                auth_header = header[1].decode("utf-8")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:].strip()
                break

        if not token:
            scope["user"] = AnonymousUser()
            return await super().__call__(scope, receive, send)

        try:
            UntypedToken(token)  # Проверяем валидность токена
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            scope["user"] = await get_user(validated_token=decoded_data)
        except (InvalidToken, TokenError) as e:
            logger.error(f"Token authentication failed: {e}")
            scope["user"] = AnonymousUser()

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
