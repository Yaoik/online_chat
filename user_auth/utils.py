from datetime import timedelta

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class CustomRefreshToken(RefreshToken):
    @classmethod
    def for_user_with_lifetime(cls, user, lifetime=timedelta(seconds=30)):
        """
        Создаёт refresh-токен для пользователя с указанным временем жизни.
        """
        token = cls.for_user(user)
        token.set_exp(lifetime=lifetime)
        return token


class CustomAccessToken(AccessToken):

    @classmethod
    def for_websocket(cls, user, lifetime=timedelta(seconds=30)):
        """
        Создаёт acess-токен для пользователя для использования в websocket.
        """
        token = cls.for_user(user)
        token.set_exp(lifetime=lifetime)
        token['for_websocket'] = True
        return token
