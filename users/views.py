import logging

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import UserSerializer

logger = logging.getLogger(__name__)


class UserMeView(APIView):
    """
    Получить данные о текущем пользователе.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(
        request=None,
        responses=UserSerializer
    )
    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)
