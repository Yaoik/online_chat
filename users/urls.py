from django.urls import path

from .views import UserMeView

urlpatterns = [
    path('api/me/', UserMeView.as_view(), name='me'),
]
