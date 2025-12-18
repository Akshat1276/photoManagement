from rest_framework import serializers
from core.models import Event

class EventSerializer(serializers.ModelSerializer):
	created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
	class Meta:
		model = Event
		fields = [
			"id",
			"title",
			"slug",
			"description",
			"start_datetime",
			"end_datetime",
			"cover_url",
			"created_by",
			"created_by_email",
			"created_at",
		]
		read_only_fields = ["id", "created_by", "created_by_email", "created_at"]