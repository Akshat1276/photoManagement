from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import UserNotification
from core.notifications.serializers import UserNotificationSerializer

class NotificationListView(generics.ListAPIView):
	serializer_class = UserNotificationSerializer
	permission_classes = [IsAuthenticated]
	def get_queryset(self):
		return (
			UserNotification.objects.filter(user=self.request.user)
			.select_related("notification", "notification__photo", "notification__event")
			.order_by("-created_at")
		)

class NotificationMarkReadView(APIView):
	permission_classes = [IsAuthenticated]
	def post(self, request, pk):
		user_notif = generics.get_object_or_404(
			UserNotification, pk=pk, user=request.user
		)
		if not user_notif.is_read:
			user_notif.is_read = True
			user_notif.save(update_fields=["is_read"])
		return Response({"detail": "Notification marked as read."}, status=status.HTTP_200_OK)