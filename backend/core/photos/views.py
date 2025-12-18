from django.db.models import Count, Q
from django.utils.dateparse import parse_datetime
from rest_framework import generics, status
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
	UserNotification,
)
from core.photos.serializers import CommentSerializer, PhotoSerializer

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

		# Basic filters
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
			UserNotification.objects.create(
				user=photo.uploaded_by,
				notification=notification,
			)
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
			UserNotification.objects.create(
				user=photo.uploaded_by,
				notification=notification,
			)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Comment.objects.all().order_by("-created_at")
	serializer_class = CommentSerializer
	permission_classes = [IsOwnerOrReadOnly]