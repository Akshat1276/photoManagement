from rest_framework import generics, permissions
from core.common.permissions import IsEventCoordinatorOrAbove, IsOwnerOrReadOnly
from core.models import Event
from .serializers import EventSerializer

class EventListCreateView(generics.ListCreateAPIView):
	queryset = Event.objects.all().order_by("-start_datetime")
	serializer_class = EventSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsEventCoordinatorOrAbove]

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user)

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Event.objects.all()
	serializer_class = EventSerializer
	permission_classes = [IsOwnerOrReadOnly]