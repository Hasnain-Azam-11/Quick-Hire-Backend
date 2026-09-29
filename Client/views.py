from rest_framework import generics, permissions, viewsets
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied

from .models import ClientProfile, JobPost
from .serializer import ClientProfileSerializer, PostjobSerializer
from .permissions import IsJobOwnerOrReadOnly


class ClientRegistrationView(generics.CreateAPIView):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.AllowAny]


class PostjobView(viewsets.ModelViewSet):
    queryset = JobPost.objects.all()
    serializer_class = PostjobSerializer
    permission_classes = [permissions.IsAuthenticated, IsJobOwnerOrReadOnly]

    def perform_create(self, serializer):
        try:
            client = self.request.user.client_profile
        except ObjectDoesNotExist:
            raise PermissionDenied("Only clients can post jobs.")
        serializer.save(client=client)