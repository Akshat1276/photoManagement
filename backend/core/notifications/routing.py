from django.urls import path
from .consumers import CommentStreamConsumer, NotificationConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    path("ws/photos/<int:photo_id>/comments/", CommentStreamConsumer.as_asgi()),
]
