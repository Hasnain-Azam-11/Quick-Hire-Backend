import django_filters
from django.template.context_processors import request
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, viewsets
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter

from . import serializer
from .models import ClientProfile, JobPost
from .serializer import ClientProfileSerializer, PostjobSerializer ,MeSerializer
from .permissions import IsJobOwnerOrReadOnly

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from .ClientFilters import JobPostFilters
from .pagination import JobPagination



class ClientRegistrationView(generics.CreateAPIView):
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.AllowAny]


class PostjobView(viewsets.ModelViewSet):
    queryset = JobPost.objects.select_related('client__user')
    serializer_class = PostjobSerializer
    permission_classes = [permissions.IsAuthenticated, IsJobOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend , OrderingFilter]
    filterset_class = JobPostFilters
    ordering_fields = ['created_at' , 'price' , 'start_date']
    pagination_class = JobPagination

    def get_queryset(self):
        query_set = JobPost.objects.select_related('client__user')
        mine = self.request.query_params.get('mine' , None)

        if mine == 'true':
            try:
                client_profile =  self.request.user.client_profile
            except ObjectDoesNotExist:
                return query_set.none()
            query_set = query_set.filter(client = client_profile)
        return query_set


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

