from django.urls import path
from core.photos.views import (
	CommentDetailView,
	MyFavouritesView,
	MyLikesView,
	MyUploadsView,
	PhotoCommentListCreateView,
	PhotoDetailView,
	PhotoFavouriteView,
	PhotoLikeView,
	PhotoListCreateView,
	PhotoBatchUploadView,
	PhotoBatchOperationsView,
	PhotoDownloadView,
	PhotoDownloadMultipleView,
	PhotosOfMeView,
)

urlpatterns = [
	path("", PhotoListCreateView.as_view(), name="photo-list-create"),
	path("batch-upload/", PhotoBatchUploadView.as_view(), name="photo-batch-upload"),
	path("batch-operations/", PhotoBatchOperationsView.as_view(), name="photo-batch-operations"),
	path("my-uploads/", MyUploadsView.as_view(), name="photo-my-uploads"),
	path("my-favourites/", MyFavouritesView.as_view(), name="photo-my-favourites"),
	path("my-likes/", MyLikesView.as_view(), name="photo-my-likes"),
	path("photos-of-me/", PhotosOfMeView.as_view(), name="photos-of-me"),
	path("<int:pk>/", PhotoDetailView.as_view(), name="photo-detail"),
	path("<int:pk>/like/", PhotoLikeView.as_view(), name="photo-like"),
	path("<int:pk>/favourite/", PhotoFavouriteView.as_view(), name="photo-favourite"),
	path("<int:pk>/comments/", PhotoCommentListCreateView.as_view(), name="photo-comments"),
	path("comments/<int:pk>/", CommentDetailView.as_view(), name="comment-detail"),

	# Download endpoints
	path("<int:pk>/download/", PhotoDownloadView.as_view(), name="photo-download"),
	path("download-multiple/", PhotoDownloadMultipleView.as_view(), name="photo-download-multiple"),
]