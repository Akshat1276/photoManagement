from rest_framework import serializers
from core.models import Comment, Photo

class PhotoSerializer(serializers.ModelSerializer):
	uploaded_by_email = serializers.EmailField(
		source="uploaded_by.email", read_only=True
	)
	uploaded_by_name = serializers.CharField(
		source="uploaded_by.profile.full_name", read_only=True
	)
	likes_count = serializers.IntegerField(source="likes.count", read_only=True)
	favourites_count = serializers.IntegerField(
		source="favourites.count", read_only=True
	)
	comments_count = serializers.IntegerField(
		source="comments.count", read_only=True
	)
	liked_by_user = serializers.SerializerMethodField()
	favourited_by_user = serializers.SerializerMethodField()

	def get_liked_by_user(self, obj):
		user = self.context.get("request").user if self.context.get("request") else None
		if not user or not user.is_authenticated:
			return False
		return obj.likes.filter(user=user).exists()

	def get_favourited_by_user(self, obj):
		user = self.context.get("request").user if self.context.get("request") else None
		if not user or not user.is_authenticated:
			return False
		return obj.favourites.filter(user=user).exists()

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
			"uploaded_by_name",
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
			"liked_by_user",
			"favourited_by_user",
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
			"liked_by_user",
			"favourited_by_user",
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