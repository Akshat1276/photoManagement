from django.urls import path
from core.notifications.views import NotificationListView, NotificationMarkReadView

urlpatterns = [
	path("", NotificationListView.as_view(), name="notification-list"),
	path(
		"<int:pk>/read/",
		NotificationMarkReadView.as_view(),
		name="notification-mark-read",
	),
]