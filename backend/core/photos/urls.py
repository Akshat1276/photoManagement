from django.urls import path
from core.photos.views import (
	CommentDetailView,
	MyFavouritesView,
	MyUploadsView,
	PhotoCommentListCreateView,
	PhotoDetailView,
	PhotoFavouriteView,
	PhotoLikeView,
	PhotoListCreateView,
	PhotoBatchUploadView,
	PhotoBatchOperationsView,
)

urlpatterns = [
	path("", PhotoListCreateView.as_view(), name="photo-list-create"),
	path("batch-upload/", PhotoBatchUploadView.as_view(), name="photo-batch-upload"),
	path("batch-operations/", PhotoBatchOperationsView.as_view(), name="photo-batch-operations"),
	path("my-uploads/", MyUploadsView.as_view(), name="photo-my-uploads"),
	path("my-favourites/", MyFavouritesView.as_view(), name="photo-my-favourites"),
	path("<int:pk>/", PhotoDetailView.as_view(), name="photo-detail"),
	path("<int:pk>/like/", PhotoLikeView.as_view(), name="photo-like"),
	path("<int:pk>/favourite/", PhotoFavouriteView.as_view(), name="photo-favourite"),
	path("<int:pk>/comments/", PhotoCommentListCreateView.as_view(), name="photo-comments"),
	path("comments/<int:pk>/", CommentDetailView.as_view(), name="comment-detail"),
]