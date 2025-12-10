from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models


class UserManager(BaseUserManager):
	use_in_migrations = True

	def _create_user(self, email, password, **extra_fields):
		if not email:
			raise ValueError("The Email field must be set")
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, email, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", False)
		extra_fields.setdefault("is_superuser", False)
		return self._create_user(email, password, extra_fields=extra_fields)

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault("is_staff", True)
		extra_fields.setdefault("is_superuser", True)

		if extra_fields.get("is_staff") is not True:
			raise ValueError("Superuser must have is_staff=True.")
		if extra_fields.get("is_superuser") is not True:
			raise ValueError("Superuser must have is_superuser=True.")

		return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
	username = None
	email = models.EmailField(unique=True)
	is_verified = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS: list[str] = []

	objects = UserManager()

	def __str__(self) -> str:
		return self.email


class Profile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	full_name = models.CharField(max_length=255)
	bio = models.TextField(blank=True)
	batch = models.CharField(max_length=50, blank=True)
	department = models.CharField(max_length=100, blank=True)
	profile_pic_url = models.URLField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.full_name or str(self.user)


class Role(models.Model):
	name = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)

	def __str__(self) -> str:
		return self.name


class UserRole(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	role = models.ForeignKey(Role, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ("user", "role")

	def __str__(self) -> str:
		return f"{self.user} -> {self.role}"


class Event(models.Model):
	title = models.CharField(max_length=255)
	slug = models.SlugField(unique=True)
	description = models.TextField(blank=True)
	start_datetime = models.DateTimeField()
	end_datetime = models.DateTimeField(null=True, blank=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="created_events",
	)
	cover_url = models.URLField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.title


class Photo(models.Model):
	class Visibility(models.TextChoices):
		PUBLIC = "public", "Public"
		PRIVATE = "private", "Private"
		EVENT_ONLY = "event_only", "Event Only"
		ROLE_BASED = "role_based", "Role Based"

	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="photos")
	uploaded_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="uploaded_photos",
	)
	image_original = models.ImageField(upload_to="photos/originals/")
	image_thumbnail = models.ImageField(
		upload_to="photos/thumbnails/", blank=True, null=True
	)
	image_watermarked = models.ImageField(
		upload_to="photos/watermarked/", blank=True, null=True
	)
	taken_at = models.DateTimeField(null=True, blank=True)
	camera_model = models.CharField(max_length=255, blank=True)
	visibility = models.CharField(
		max_length=20,
		choices=Visibility.choices,
		default=Visibility.PUBLIC,
	)
	metadata = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"Photo {self.id} ({self.event})"


class Tag(models.Model):
	class TagType(models.TextChoices):
		MANUAL = "manual", "Manual"
		AI = "ai", "AI"

	name = models.CharField(max_length=100)
	tag_type = models.CharField(
		max_length=10,
		choices=TagType.choices,
		default=TagType.MANUAL,
	)
	confidence = models.FloatField(
		null=True,
		blank=True,
		validators=[MinValueValidator(0.0)],
	)

	class Meta:
		unique_together = ("name", "tag_type")

	def __str__(self) -> str:
		return self.name


class PhotoTag(models.Model):
	photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="photo_tags")
	tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="tag_photos")

	class Meta:
		unique_together = ("photo", "tag")

	def __str__(self) -> str:
		return f"{self.photo_id} - {self.tag_id}"


class PhotoUser(models.Model):
	photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="detected_users")
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	confidence_score = models.FloatField(
		null=True,
		blank=True,
		validators=[MinValueValidator(0.0)],
	)

	class Meta:
		unique_together = ("photo", "user")

	def __str__(self) -> str:
		return f"{self.user} in {self.photo_id}"


class Favourite(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="favourites")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ("user", "photo")

	def __str__(self) -> str:
		return f"{self.user} favourited {self.photo_id}"


class Like(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="likes")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ("user", "photo")

	def __str__(self) -> str:
		return f"{self.user} liked {self.photo_id}"


class Comment(models.Model):
	photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="comments")
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	parent_comment = models.ForeignKey(
		"self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
	)
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"Comment {self.id} on {self.photo_id}"


class Notification(models.Model):
	type = models.CharField(max_length=50)
	message = models.TextField()
	photo = models.ForeignKey(
		Photo,
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name="notifications",
	)
	event = models.ForeignKey(
		Event,
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name="notifications",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return f"Notification {self.id}: {self.type}"


class UserNotification(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	notification = models.ForeignKey(
		Notification, on_delete=models.CASCADE, related_name="user_notifications"
	)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ("user", "notification")

	def __str__(self) -> str:
		return f"Notif {self.notification_id} -> {self.user}"