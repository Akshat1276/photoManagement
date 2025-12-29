import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from core.models import UserNotification
from core.notifications.serializers import UserNotificationSerializer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if user.is_anonymous:
            await self.close()
            return

        self.group_name = f"notifications_{user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # Optional: send unread notifications on connect
        unread = await self.get_unread_notifications(user)
        await self.send_json({
            "type": "initial_notifications",
            "data": unread
        })

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        """
        Handle messages from client if needed.
        Example: mark notifications as read.
        """
        pass

    async def notify(self, event):
        """
        Called via channel_layer.group_send
        """
        await self.send_json(event["data"])

    @database_sync_to_async
    def get_unread_notifications(self, user):
        qs = UserNotification.objects.filter(
            user=user,
            is_read=False
        ).order_by("-created_at")

        return UserNotificationSerializer(qs, many=True).data
