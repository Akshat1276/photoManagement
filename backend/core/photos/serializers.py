from rest_framework import serializers
from core.models import Comment, Photo

class PhotoSerializer(serializers.ModelSerializer):
	uploaded_by_email = serializers.EmailField(
		source="uploaded_by.email", read_only=True
	)
	likes_count = serializers.IntegerField(source="likes.count", read_only=True)
	favourites_count = serializers.IntegerField(
		source="favourites.count", read_only=True
	)
	comments_count = serializers.IntegerField(
		source="comments.count", read_only=True
	)

	def validate_metadata(self, value):
		if value in (None, "", {}):
			return {}
		return value

	class Meta:
		model = Photo
		fields = [
			"id",
			"event",
			"uploaded_by",
			"uploaded_by_email",
			"image_original",
			"image_thumbnail",
			"image_watermarked",
			"taken_at",
			"camera_model",
			"visibility",
			"metadata",
			"created_at",
			"likes_count",
			"favourites_count",
			"comments_count",
		]
		read_only_fields = [
			"id",
			"uploaded_by",
			"uploaded_by_email",
			"image_thumbnail",
			"image_watermarked",
			"created_at",
			"likes_count",
			"favourites_count",
			"comments_count",
		]

class CommentSerializer(serializers.ModelSerializer):
	user_email = serializers.EmailField(source="user.email", read_only=True)
	class Meta:
		model = Comment
		fields = [
			"id",
			"photo",
			"user",
			"user_email",
			"parent_comment",
			"content",
			"created_at",
		]
		read_only_fields = [
			"id",
			"photo",
			"user",
			"user_email",
			"created_at",
		]