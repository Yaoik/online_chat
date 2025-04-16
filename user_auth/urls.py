from django.urls import include, path, re_path

urlpatterns = (
    re_path(r'^api/auth1/', include('social_django.urls', namespace="social")),
    re_path(r'^api/auth/', include('drf_social_oauth2.urls', namespace='drf')),
)