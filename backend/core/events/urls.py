from django.urls import path
from core.photos.views import EventPhotoListView
from .views import EventDetailView, EventListCreateView

urlpatterns = [
	path("", EventListCreateView.as_view(), name="event-list-create"),
	path("<slug:slug>/", EventDetailView.as_view(), name="event-detail"),
	path("<slug:slug>/photos/", EventPhotoListView.as_view(), name="event-photo-list"),
]