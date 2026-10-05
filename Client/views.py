from rest_framework import generics, permissions, viewsets
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied

from . import serializer
from .models import ClientProfile, JobPost
from .serializer import ClientProfileSerializer, PostjobSerializer ,MeSerializer
from .permissions import IsJobOwnerOrReadOnly

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response


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

class MeView(generics.RetrieveUpdateAPIView):

    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            client =  self.request.user.client_profile
        except ObjectDoesNotExist:
            raise PermissionDenied("Client Profile does not exists")
        return client

class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data = request.data , context={'request' : request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token , created = Token.objects.get_or_create(user = user)

        try:
            client_profile = user.client_profile
        except ObjectDoesNotExist:
            client_profile =None

        try:
            worker_bio = user.client_profile.worker_bio if client_profile else None
        except ObjectDoesNotExist:
            worker_bio = None

        return Response( {
            'token' : token.key,
            'client_profile_id' : client_profile.id if client_profile else None,
            'worker_Bio_id' : worker_bio.id if worker_bio else None,
            'is_worker' : worker_bio is not None,
        })

