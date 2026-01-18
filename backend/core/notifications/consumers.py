import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from core.models import Photo, UserNotification
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


class CommentStreamConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.photo_id = self.scope["url_route"]["kwargs"].get("photo_id")
        user = self.scope.get("user")

        can_view = await self._user_can_view_photo(user, self.photo_id)
        if not can_view:
            await self.close()
            return

        self.group_name = f"photo_comments_{self.photo_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        """Currently read-only stream; ignore client messages."""
        return

    async def comment_event(self, event):
        """Forward comment events to the client."""
        await self.send_json(event["data"])

    @database_sync_to_async
    def _user_can_view_photo(self, user, photo_id):
        if not photo_id:
            return False

        qs = Photo.objects.filter(pk=photo_id)

        if not user or not getattr(user, "is_authenticated", False):
            # Guests: never see private photos
            qs = qs.exclude(visibility=Photo.Visibility.PRIVATE)
        else:
            # Authenticated users: see all non-private photos, plus their own private
            qs = qs.filter(
                Q(
                    visibility__in=[
                        Photo.Visibility.PUBLIC,
                        Photo.Visibility.EVENT_ONLY,
                        Photo.Visibility.ROLE_BASED,
                    ]
                )
                | Q(visibility=Photo.Visibility.PRIVATE, uploaded_by=user)
            )

        return qs.exists()
