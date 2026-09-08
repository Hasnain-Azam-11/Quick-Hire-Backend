from rest_framework import generics, permissions, viewsets
from .models import ClientProfile, JobPost
from .serializer import ClientProfileSerializer,PostjobSerializer  # ✅ serializer → serializers (import name)
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
        serializer.save(client=self.request.user.client_profile)