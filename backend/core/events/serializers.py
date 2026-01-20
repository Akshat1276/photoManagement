
from rest_framework import serializers
from core.models import Event, Photo


# Serializer for Photo model (event photos)
class PhotoSerializer(serializers.ModelSerializer):
	class Meta:
		model = Photo
		fields = [
			"id",
			"image_original",
			"image_thumbnail",
			"image_watermarked",
		]

class EventSerializer(serializers.ModelSerializer):
	created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
	photos = PhotoSerializer(many=True, read_only=True)
	photographers = serializers.SerializerMethodField()
	coordinators = serializers.SerializerMethodField()

	def get_photographers(self, obj):
		return [u.email for u in obj.photographers.all()]

	def get_coordinators(self, obj):
		return [u.email for u in obj.coordinators.all()]

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
			"photos",  # Include related photos
			"created_by",
			"created_by_email",
			"created_at",
			"photographers",
			"coordinators",
		]
		read_only_fields = ["id", "created_by", "created_by_email", "created_at", "photographers", "coordinators"]