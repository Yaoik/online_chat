import logging

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from user_auth.utils import CustomAccessToken

from .serializers import TokenResponseSerializer

logger = logging.getLogger(__name__)


class WebsocketTokenView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: TokenResponseSerializer,
        },
    )
    def get(self, requets: Request, *args, **kwargs):
        user = requets.user
        token = CustomAccessToken.for_websocket(user)
        return Response({'token': str(token)}, status=status.HTTP_200_OK)
