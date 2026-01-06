from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.fields import ArrayField





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
		return self._create_user(email, password, **extra_fields)

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
	roles = models.ManyToManyField('Role', blank=True, related_name='users')
	face_encoding = models.JSONField(null=True, blank=True)
	photos_of_me_last_scanned_at = models.DateTimeField(null=True, blank=True)

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

class EmailVerificationCode(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	code = models.CharField(max_length=6)
	created_at = models.DateTimeField(auto_now_add=True)
	is_used = models.BooleanField(default=False)

	def is_expired(self, minutes: int = 10) -> bool:
		return timezone.now() - self.created_at > timezone.timedelta(minutes=minutes)

	def __str__(self) -> str:
		return f"OTP for {self.user} at {self.created_at:%Y-%m-%d %H:%M:%S}"


class Permission(models.Model):
	"""
	Represents a granular permission that can be assigned to roles.
	Example: 'add_event', 'edit_photo', etc.
	"""
	code = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_permissions')

	def __str__(self) -> str:
		return self.code


class Role(models.Model):
	name = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)
	permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	updated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_roles')

	def __str__(self) -> str:
		return self.name

	# Signal to auto-create Profile when a new User is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
	from .models import Profile  # Avoid circular import
	if created:
		Profile.objects.get_or_create(user=instance)




class Event(models.Model):
	def is_coordinator(self, user):
		if not user or not user.is_authenticated:
			return False
		return user.is_superuser or user in self.coordinators.all()

	def is_photographer(self, user):
		if not user or not user.is_authenticated:
			return False
		return user.is_superuser or user in self.photographers.all()

	def is_admin(self, user):
		return user and user.is_authenticated and user.roles.filter(name__iexact="admin").exists()

	def is_img_member(self, user):
		return user and user.is_authenticated

	def can_manage_event(self, user):
		return self.is_admin(user) or self.is_coordinator(user)
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
	coordinators = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		blank=True,
		related_name="coordinated_events"
	)
	photographers = models.ManyToManyField(
		settings.AUTH_USER_MODEL,
		blank=True,
		related_name="photographed_events"
	)
	cover_url = models.URLField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self) -> str:
		return self.title


class Photo(models.Model):
	def can_edit(self, user):
		if not user or not user.is_authenticated:
			return False
		# Global high-privilege checks
		if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
			return True
		# Custom Admin role for this project (event-level helper checks role "Admin")
		if self.event.is_admin(user):
			return True
		# Event coordinators can manage photos in their events
		if self.event.is_coordinator(user):
			return True
		# Fallback: only the uploader can edit
		return self.uploaded_by == user

	def can_delete(self, user):
		return self.can_edit(user)

	def can_download(self, user, variant="original"):
		from django.utils import timezone
		if not user or not user.is_authenticated:
			# Only allow guests to download public watermarked
			return self.visibility == self.Visibility.PUBLIC and variant != "original" and self._within_time_window()
		# Hard privacy: private photos are only downloadable by their uploader
		if self.visibility == self.Visibility.PRIVATE and self.uploaded_by != user:
			return False
		# Global high-privilege checks: superusers, staff, and custom Admin role
		if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
			return True
		if self.event.is_admin(user):
			return True
		# Event coordinators and photographers always allowed
		if self.event.is_coordinator(user):
			return True
		if self.event.is_photographer(user):
			return True
		# All registered users are IMG members
		if not self._within_time_window():
			return False
		if variant == "original":
			return self.visibility in [self.Visibility.PUBLIC, self.Visibility.EVENT_ONLY, self.Visibility.ROLE_BASED, self.Visibility.PRIVATE]
		else:
			return self.visibility in [self.Visibility.PUBLIC, self.Visibility.EVENT_ONLY, self.Visibility.ROLE_BASED]

	def _within_time_window(self, days=30):
		from django.utils import timezone
		if not self.created_at:
			return False
		return (timezone.now() - self.created_at).days < days
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