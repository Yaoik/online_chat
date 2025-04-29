from django.urls import include, path, re_path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import WebsocketTokenView

urlpatterns = (
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/websocket/', WebsocketTokenView.as_view(), name='websocket_token'),

    re_path(r'^api/auth/social/', include('social_django.urls', namespace="social")),
    re_path(r'^api/auth/', include('drf_social_oauth2.urls', namespace='drf')),
)
