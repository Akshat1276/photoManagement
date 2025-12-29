import os
from core.models import Photo
from django.http import FileResponse, Http404, StreamingHttpResponse
from django.conf import settings
import zipfile
from io import BytesIO
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import generics
from core.photos.serializers import PhotoSerializer
from rest_framework.permissions import IsAuthenticated


# ...existing code...


# Proper DRF view for 'Photos of Me'
class PhotosOfMeView(generics.ListAPIView):
	serializer_class = PhotoSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		print("PhotosOfMeView: started")
		user = self.request.user
		if not hasattr(user, "face_encoding") or not user.face_encoding:
			print("No face encoding")
			return Photo.objects.none()
		import numpy as np
		import face_recognition
		from PIL import Image
		encoding = np.array(user.face_encoding)
		print(f"User face_encoding (first 5): {encoding[:5]}")
		matched_photo_ids = []
		for photo in Photo.objects.all():
			print(f"Processing photo {photo.id}")
			img_field = photo.image_original
			if not img_field:
				print(f"Photo {photo.id} has no image.")
				continue
			try:
				img_field.open('rb')
				img_field.seek(0)
				print(f"Photo {photo.id}: name={img_field.name}, size={getattr(img_field, 'size', 'unknown')}")
				first_bytes = img_field.read(10)
				print(f"Photo {photo.id}: first 10 bytes: {first_bytes}")
				img_field.seek(0)
				import io
				from PIL import Image, ExifTags
				# Read all bytes from the image field
				image_bytes = img_field.read()
				pil_image = Image.open(io.BytesIO(image_bytes))
				# Handle EXIF orientation
				try:
					for orientation in ExifTags.TAGS.keys():
						if ExifTags.TAGS[orientation] == 'Orientation':
							break
					exif = pil_image._getexif()
					if exif is not None:
						orientation_value = exif.get(orientation, None)
						if orientation_value == 3:
							pil_image = pil_image.rotate(180, expand=True)
						elif orientation_value == 6:
							pil_image = pil_image.rotate(270, expand=True)
						elif orientation_value == 8:
							pil_image = pil_image.rotate(90, expand=True)
				except Exception as ex:
					print(f"[DEBUG] EXIF orientation handling failed: {ex}")
				pil_image = pil_image.convert('RGB')
				import numpy as np
				img_np = np.array(pil_image)
			except Exception as e:
				import traceback
				print(f"Error loading photo {photo.id}: {e}")
				traceback.print_exc()
				continue
			encodings = face_recognition.face_encodings(img_np)
			print(f"Photo {photo.id}: found {len(encodings)} faces")
			for enc in encodings:
				print(f"Photo {photo.id}: encoding (first 5): {enc[:5]}")
				match = face_recognition.compare_faces([encoding], enc, tolerance=0.6)[0]
				print(f"Photo {photo.id}: match={match}")
				if match:
					matched_photo_ids.append(photo.id)
					break
		print(f"PhotosOfMeView: finished, matched {len(matched_photo_ids)} photos")
		return Photo.objects.filter(id__in=matched_photo_ids).order_by("-created_at")


class PhotoDownloadView(APIView):
	permission_classes = [IsAuthenticatedOrReadOnly]

	def get(self, request, pk):
		"""Download a single photo (original or watermarked) with permission checks."""
		variant = request.query_params.get("variant", "watermarked")
		try:
			photo = Photo.objects.get(pk=pk)
		except Photo.DoesNotExist:
			raise Http404("Photo not found")

		user = request.user
		if not photo.can_download(user, variant=variant):
			return Response({"detail": "You do not have permission to download this image."}, status=403)
		if variant == "original":
			file_field = photo.image_original
		else:
			file_field = photo.image_watermarked or photo.image_thumbnail
			if not file_field:
				return Response({"detail": "No watermarked image available."}, status=404)
		if not file_field:
			return Response({"detail": "Image file not found."}, status=404)
		filename = os.path.basename(file_field.name)
		response = FileResponse(file_field.open(), as_attachment=True, filename=filename)
		return response


class PhotoDownloadMultipleView(APIView):
	permission_classes = [IsAuthenticatedOrReadOnly]

	def post(self, request):
		"""Download multiple photos as a zip (with permission checks)."""
		ids = request.data.get("photo_ids")
		variant = request.data.get("variant", "watermarked")
		if not isinstance(ids, list) or not ids:
			return Response({"detail": "photo_ids must be a non-empty list."}, status=400)
		photos = Photo.objects.filter(id__in=ids)
		user = request.user
		files = []
		for photo in photos:
			if not photo.can_download(user, variant=variant):
				continue
			if variant == "original":
				file_field = photo.image_original
			else:
				file_field = photo.image_watermarked or photo.image_thumbnail
			if file_field:
				files.append((os.path.basename(file_field.name), file_field))

		if not files:
			return Response({"detail": "No permitted images found for download."}, status=404)

		zip_buffer = BytesIO()
		with zipfile.ZipFile(zip_buffer, "w") as zip_file:
			for fname, file_field in files:
				file_field.open("rb")
				with file_field:
					zip_file.writestr(fname, file_field.read())
		zip_buffer.seek(0)
		response = StreamingHttpResponse(zip_buffer, content_type="application/zip")
		response["Content-Disposition"] = 'attachment; filename="photos.zip"'
		return response
from django.db.models import Count, Q
from django.utils.dateparse import parse_datetime
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import (
	IsAuthenticated,
	IsAuthenticatedOrReadOnly,
	SAFE_METHODS,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from core.common.permissions import IsOwnerOrReadOnly, IsPhotographerOrAbove
from core.tasks import process_photo
from core.models import (
	Comment,
	Event,
	Favourite,
	Like,
	Notification,
	Photo,
	PhotoTag,
	Tag,
	UserNotification,
)

from core.photos.serializers import CommentSerializer, PhotoSerializer
from core.notifications.services import send_email_notification

class PhotoListCreateView(generics.ListCreateAPIView):
	queryset = Photo.objects.all()
	serializer_class = PhotoSerializer
	permission_classes = [IsAuthenticatedOrReadOnly, IsPhotographerOrAbove]

	def get_permissions(self):
		if self.request.method in SAFE_METHODS:
			return [IsAuthenticatedOrReadOnly()]
		return [IsAuthenticated(), IsPhotographerOrAbove()]
	def get_queryset(self):
		qs = Photo.objects.all()
		params = self.request.query_params
		user = self.request.user

		# Visibility enforcement
		if not user.is_authenticated:
			# Anonymous users: only public photos
			qs = qs.filter(visibility=Photo.Visibility.PUBLIC)
		elif user.is_staff or user.is_superuser:
			# Staff/admin: see all
			pass
		else:
			# Authenticated users: public, their own private, event_only if event member, role_based if role
			public = Q(visibility=Photo.Visibility.PUBLIC)
			own_private = Q(visibility=Photo.Visibility.PRIVATE, uploaded_by=user)
			# Event membership: user is in event's members (assume event.members or fallback to event__photos__uploaded_by=user)
			event_only = Q(visibility=Photo.Visibility.EVENT_ONLY, event__photos__uploaded_by=user)
			# Role-based: user has any role required (assume user.roles exists)
			from core.common.utils import user_has_any_role
			# For now, allow all role_based to users with any role (customize as needed)
			user_roles = list(user.roles.values_list("name", flat=True)) if hasattr(user, "roles") else []
			role_based = Q(visibility=Photo.Visibility.ROLE_BASED)
			if user_roles:
				qs = qs.filter(public | own_private | event_only | role_based)
			else:
				qs = qs.filter(public | own_private | event_only)

		# Basic filters (unchanged)
		event_id = params.get("event")
		event_slug = params.get("event_slug")
		uploaded_by = params.get("uploaded_by")
		camera_model = params.get("camera_model")
		visibility = params.get("visibility")
		search = params.get("q")

		if event_id:
			qs = qs.filter(event_id=event_id)
		if event_slug:
			qs = qs.filter(event__slug=event_slug)
		if uploaded_by:
			qs = qs.filter(uploaded_by_id=uploaded_by)
		if camera_model:
			qs = qs.filter(camera_model__icontains=camera_model)
		if visibility:
			qs = qs.filter(visibility=visibility)

		taken_from = params.get("taken_from")
		taken_to = params.get("taken_to")
		created_from = params.get("created_from")
		created_to = params.get("created_to")

		if taken_from:
			start_dt = parse_datetime(taken_from)
			if start_dt:
				qs = qs.filter(taken_at__gte=start_dt)
		if taken_to:
			end_dt = parse_datetime(taken_to)
			if end_dt:
				qs = qs.filter(taken_at__lte=end_dt)
		if created_from:
			start_created = parse_datetime(created_from)
			if start_created:
				qs = qs.filter(created_at__gte=start_created)
		if created_to:
			end_created = parse_datetime(created_to)
			if end_created:
				qs = qs.filter(created_at__lte=end_created)

		if search:
			qs = qs.filter(
				Q(event__title__icontains=search)
				| Q(camera_model__icontains=search)
			)

		sort = params.get("sort", "newest")
		if sort == "oldest":
			qs = qs.order_by("created_at")
		elif sort == "most_liked":
			qs = qs.annotate(_likes_count=Count("likes")).order_by("-_likes_count", "-created_at")
		elif sort == "most_favourited":
			qs = qs.annotate(_favourites_count=Count("favourites")).order_by("-_favourites_count", "-created_at")
		elif sort == "most_commented":
			qs = qs.annotate(_comments_count=Count("comments")).order_by("-_comments_count", "-created_at")
		else:
			qs = qs.order_by("-created_at")

		return qs

	def perform_create(self, serializer):
		photo = serializer.save(uploaded_by=self.request.user)
		process_photo.delay(photo.id)
		# Trigger face extraction (async)
		from core.photos.face_tasks import extract_faces_for_photo
		extract_faces_for_photo.delay(photo.id)
		# Notify event members (except uploader) of new upload
		if photo.event:
			from core.notifications.services import send_realtime_notification
			from core.models import User
			event_members = User.objects.filter(photo__event=photo.event).distinct()
			for user in event_members:
				if user != self.request.user:
					notification = Notification.objects.create(
						type="photo_upload",
						message=f"{self.request.user.email} uploaded a new photo to event {photo.event.title}.",
						photo=photo,
						event=photo.event,
					)
					user_notif = UserNotification.objects.create(user=user, notification=notification)
					send_realtime_notification(user_notif)
					send_email_notification(user_notif)

class PhotoBatchUploadView(APIView):
	permission_classes = [IsAuthenticated, IsPhotographerOrAbove]
	parser_classes = [MultiPartParser, FormParser]
	def post(self, request):
		event_id = request.data.get("event")
		if not event_id:
			return Response(
				{"detail": "'event' is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)
		try:
			event = Event.objects.get(pk=event_id)
		except Event.DoesNotExist:
			return Response(
				{"detail": "Event not found."},
				status=status.HTTP_404_NOT_FOUND,
			)
		user = request.user
		if not (event.is_photographer(user) or event.is_coordinator(user) or event.is_admin(user)):
			return Response({"detail": "You do not have permission to upload photos to this event."}, status=403)
		files = request.FILES.getlist("images")
		if not files:
			return Response(
				{"detail": "No files provided. Use the 'images' field with one or more files."},
				status=status.HTTP_400_BAD_REQUEST,
			)
		visibility = request.data.get("visibility", Photo.Visibility.PUBLIC)
		created_photos = []
		from core.notifications.services import send_realtime_notification
		from core.models import User, Notification, UserNotification
		from core.photos.face_tasks import extract_faces_for_photo
		for file_obj in files:
			photo = Photo.objects.create(
				event=event,
				uploaded_by=request.user,
				image_original=file_obj,
				visibility=visibility,
			)
			created_photos.append(photo)
			process_photo.delay(photo.id)
			extract_faces_for_photo.delay(photo.id)
			# Notify event members (except uploader) of new upload
			if event:
				event_members = User.objects.filter(uploaded_photos__event=event).distinct()
				for user in event_members:
					if user != request.user:
						notification = Notification.objects.create(
							type="photo_upload",
							message=f"{request.user.email} uploaded a new photo to event {event.title}.",
							photo=photo,
							event=event,
						)
						user_notif = UserNotification.objects.create(user=user, notification=notification)
						send_realtime_notification(user_notif)
						send_email_notification(user_notif)
		serializer = PhotoSerializer(created_photos, many=True, context={"request": request})
		return Response(serializer.data, status=status.HTTP_201_CREATED)

class PhotoBatchOperationsView(APIView):
	"""Supported actions:
	- delete: remove selected photos.
	- move: change their event (requires ``target_event``).
	- update_visibility: change visibility (requires ``visibility``).
	- set_tags: replace manual tags (requires ``tags`` list of strings)."""
	permission_classes = [IsAuthenticated, IsPhotographerOrAbove]
	def post(self, request):
		data = request.data
		photo_ids = data.get("photo_ids")
		action = data.get("action")
		if not isinstance(photo_ids, list) or not photo_ids:
			return Response(
				{"detail": "'photo_ids' must be a non-empty list of IDs."},
				status=status.HTTP_400_BAD_REQUEST,
			)
		if not action:
			return Response(
				{"detail": "'action' is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)
		user = request.user
		qs = Photo.objects.filter(id__in=photo_ids)
		photos = list(qs)
		if not photos:
			return Response(
				{"detail": "No matching photos found for these IDs."},
				status=status.HTTP_404_NOT_FOUND,
			)

		# Permission enforcement per action
		if action == "delete":
			unauthorized = [p for p in photos if not p.can_delete(user)]
			if unauthorized:
				return Response({"detail": f"You do not have permission to delete {len(unauthorized)} of the selected photos."}, status=403)
			count = len(photos)
			qs.delete()
			return Response({"detail": f"Deleted {count} photos."})

		if action == "move":
			target_event_id = data.get("target_event")
			if not target_event_id:
				return Response(
					{"detail": "'target_event' is required for move action."},
					status=status.HTTP_400_BAD_REQUEST,
				)
			try:
				event = Event.objects.get(pk=target_event_id)
			except Event.DoesNotExist:
				return Response(
					{"detail": "Target event not found."},
					status=status.HTTP_404_NOT_FOUND,
				)
			# Only coordinators/admins of target event can move photos
			if not event.can_manage_event(user):
				return Response({"detail": "You do not have permission to move photos to this event."}, status=403)
			unauthorized = [p for p in photos if not p.can_edit(user)]
			if unauthorized:
				return Response({"detail": f"You do not have permission to move {len(unauthorized)} of the selected photos."}, status=403)
			qs.update(event=event)
			return Response({"detail": f"Moved {qs.count()} photos to event {event.id}."})

		if action == "update_visibility":
			visibility = data.get("visibility")
			valid_values = {choice[0] for choice in Photo.Visibility.choices}
			if visibility not in valid_values:
				return Response(
					{"detail": f"'visibility' must be one of {sorted(valid_values)}."},
					status=status.HTTP_400_BAD_REQUEST,
				)
			unauthorized = [p for p in photos if not p.can_edit(user)]
			if unauthorized:
				return Response({"detail": f"You do not have permission to change visibility for {len(unauthorized)} of the selected photos."}, status=403)
			qs.update(visibility=visibility)
			return Response({"detail": f"Updated visibility for {qs.count()} photos."})

		if action == "set_tags":
			tags = data.get("tags") or []
			if not isinstance(tags, list):
				return Response(
					{"detail": "'tags' must be a list of strings."},
					status=status.HTTP_400_BAD_REQUEST,
				)
			unauthorized = [p for p in photos if not p.can_edit(user)]
			if unauthorized:
				return Response({"detail": f"You do not have permission to tag {len(unauthorized)} of the selected photos."}, status=403)
			PhotoTag.objects.filter(photo__in=qs, tag__tag_type=Tag.TagType.MANUAL).delete()
			from core.notifications.services import send_realtime_notification
			from core.models import Notification, UserNotification
			for name in tags:
				name = str(name).strip()
				if not name:
					continue
				tag, _ = Tag.objects.get_or_create(name=name, tag_type=Tag.TagType.MANUAL)
				for photo in photos:
					PhotoTag.objects.get_or_create(photo=photo, tag=tag)
					if photo.uploaded_by != user:
						notification = Notification.objects.create(
							type="photo_tag",
							message=f"{user.email} tagged your photo with '{name}'.",
							photo=photo,
							event=photo.event,
						)
						user_notif = UserNotification.objects.create(user=photo.uploaded_by, notification=notification)
						send_realtime_notification(user_notif)
						send_email_notification(user_notif)
		if action == "delete":
			count = qs.count()
			qs.delete()
			return Response({"detail": f"Deleted {count} photos."})
		if action == "move":
			target_event_id = data.get("target_event")
			if not target_event_id:
				return Response(
					{"detail": "'target_event' is required for move action."},
					status=status.HTTP_400_BAD_REQUEST,
				)
			try:
				event = Event.objects.get(pk=target_event_id)
			except Event.DoesNotExist:
				return Response(
					{"detail": "Target event not found."},
					status=status.HTTP_404_NOT_FOUND,
				)
			qs.update(event=event)
			return Response({"detail": f"Moved {qs.count()} photos to event {event.id}."})
		if action == "update_visibility":
			visibility = data.get("visibility")
			valid_values = {choice[0] for choice in Photo.Visibility.choices}
			if visibility not in valid_values:
				return Response(
					{"detail": f"'visibility' must be one of {sorted(valid_values)}."},
					status=status.HTTP_400_BAD_REQUEST,
				)
			qs.update(visibility=visibility)
			return Response({"detail": f"Updated visibility for {qs.count()} photos."})
		if action == "set_tags":
			tags = data.get("tags") or []
			if not isinstance(tags, list):
				return Response(
					{"detail": "'tags' must be a list of strings."},
					status=status.HTTP_400_BAD_REQUEST,
				)
			PhotoTag.objects.filter(photo__in=qs, tag__tag_type=Tag.TagType.MANUAL).delete()
			from core.notifications.services import send_realtime_notification
			from core.models import Notification, UserNotification
			for name in tags:
				name = str(name).strip()
				if not name:
					continue
				tag, _ = Tag.objects.get_or_create(name=name, tag_type=Tag.TagType.MANUAL)
				for photo in photos:
					PhotoTag.objects.get_or_create(photo=photo, tag=tag)
					if photo.uploaded_by != user:
						notification = Notification.objects.create(
							type="photo_tag",
							message=f"{user.email} tagged your photo with '{name}'.",
							photo=photo,
							event=photo.event,
						)
						user_notif = UserNotification.objects.create(user=photo.uploaded_by, notification=notification)
						send_realtime_notification(user_notif)
						send_email_notification(user_notif)
			return Response({"detail": f"Updated manual tags for {len(photos)} photos."})

		return Response(
			{"detail": "Unsupported action. Use 'delete', 'move', 'update_visibility', or 'set_tags'."},
			status=status.HTTP_400_BAD_REQUEST,
		)
class PhotoDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Photo.objects.all()
	serializer_class = PhotoSerializer
	permission_classes = [IsOwnerOrReadOnly]

class MyUploadsView(generics.ListAPIView):
	serializer_class = PhotoSerializer
	permission_classes = [IsAuthenticated]
	def get_queryset(self):
		return Photo.objects.filter(uploaded_by=self.request.user).order_by("-created_at")


class MyFavouritesView(generics.ListAPIView):
	serializer_class = PhotoSerializer
	permission_classes = [IsAuthenticated]
	def get_queryset(self):
		return (
			Photo.objects.filter(favourites__user=self.request.user)
			.order_by("-created_at")
			.distinct()
		)


# New view for photos liked by the current user
class MyLikesView(generics.ListAPIView):
	serializer_class = PhotoSerializer
	permission_classes = [IsAuthenticated]
	def get_queryset(self):
		return (
			Photo.objects.filter(likes__user=self.request.user)
			.order_by("-created_at")
			.distinct()
		)

class EventPhotoListView(generics.ListAPIView):
	serializer_class = PhotoSerializer
	permission_classes = [IsAuthenticatedOrReadOnly]
	def get_queryset(self):
		event_slug = self.kwargs.get("slug")
		return Photo.objects.filter(event__slug=event_slug).order_by("-created_at")

class PhotoLikeView(APIView):
	permission_classes = [IsAuthenticated]
	def post(self, request, pk):
		photo = generics.get_object_or_404(Photo, pk=pk)
		like, created = Like.objects.get_or_create(user=request.user, photo=photo)
		if created and photo.uploaded_by != request.user:
			notification = Notification.objects.create(
				type="photo_like",
				message=f"{request.user.email} liked your photo.",
				photo=photo,
				event=photo.event,
			)
			user_notif = UserNotification.objects.create(
				user=photo.uploaded_by,
				notification=notification,
			)
			from core.notifications.services import send_realtime_notification
			send_realtime_notification(user_notif)
			send_email_notification(user_notif)
		likes_count = photo.likes.count()
		return Response(
			{"detail": "Photo liked.", "liked": True, "likes_count": likes_count},
			status=status.HTTP_200_OK,
		)
	def delete(self, request, pk):
		photo = generics.get_object_or_404(Photo, pk=pk)
		Like.objects.filter(user=request.user, photo=photo).delete()
		likes_count = photo.likes.count()
		return Response(
			{"detail": "Like removed.", "liked": False, "likes_count": likes_count},
			status=status.HTTP_200_OK,
		)

class PhotoFavouriteView(APIView):
	permission_classes = [IsAuthenticated]
	def post(self, request, pk):
		"""Mark a photo as favourite for the current user."""
		photo = generics.get_object_or_404(Photo, pk=pk)
		Favourite.objects.get_or_create(user=request.user, photo=photo)
		favourites_count = photo.favourites.count()
		return Response(
			{
				"detail": "Photo favourited.",
				"favourited": True,
				"favourites_count": favourites_count,
			},
			status=status.HTTP_200_OK,
		)
	def delete(self, request, pk):
		photo = generics.get_object_or_404(Photo, pk=pk)
		Favourite.objects.filter(user=request.user, photo=photo).delete()
		favourites_count = photo.favourites.count()
		return Response(
			{
				"detail": "Favourite removed.",
				"favourited": False,
				"favourites_count": favourites_count,
			},
			status=status.HTTP_200_OK,
		)

class PhotoCommentListCreateView(generics.ListCreateAPIView):
	serializer_class = CommentSerializer
	permission_classes = [IsAuthenticatedOrReadOnly]

	def get_queryset(self):
		photo_id = self.kwargs.get("pk")
		return Comment.objects.filter(photo_id=photo_id, parent_comment__isnull=True).order_by(
			"-created_at"
		)
	def perform_create(self, serializer):
		photo = generics.get_object_or_404(Photo, pk=self.kwargs.get("pk"))
		comment = serializer.save(user=self.request.user, photo=photo)
		if photo.uploaded_by != self.request.user:
			notification = Notification.objects.create(
				type="photo_comment",
				message=f"{self.request.user.email} commented on your photo.",
				photo=photo,
				event=photo.event,
			)
			user_notif = UserNotification.objects.create(
				user=photo.uploaded_by,
				notification=notification,
			)
			from core.notifications.services import send_realtime_notification
			send_realtime_notification(user_notif)
			send_email_notification(user_notif)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Comment.objects.all().order_by("-created_at")
	serializer_class = CommentSerializer
	permission_classes = [IsOwnerOrReadOnly]