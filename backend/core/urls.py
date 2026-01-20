from django.urls import include, path

urlpatterns = [
	path("auth/", include("core.users.urls")),
	path("events/", include("core.events.urls")),
	path("photos/", include("core.photos.urls")),
	path("notifications/", include("core.notifications.urls")),
]