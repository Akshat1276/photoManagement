from rest_framework import serializers
from core.models import Notification, UserNotification

class NotificationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notification
		fields = [
			"id",
			"type",
			"message",
			"photo",
			"event",
			"created_at",
		]
		read_only_fields = fields

class UserNotificationSerializer(serializers.ModelSerializer):
	notification = NotificationSerializer(read_only=True)
	class Meta:
		model = UserNotification
		fields = [
			"id",
			"notification",
			"is_read",
			"created_at",
		]
		read_only_fields = ["id", "notification", "created_at"]