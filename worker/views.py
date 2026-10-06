
from rest_framework import generics,permissions,viewsets
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied, ValidationError

# from Client import permissions, serializer
from .workerSerializer import WorkerBioOwnerSerializer,WorkerBioPublicSerializer,WorkerServiceSerializer
from .models import WorkerBio,WorkerService
from .workerPermissions import IsWorkerBioOrReadOnly,IsWorkerServiceOrReadOnly
# Create your views here.
class WorkerBioView(viewsets.ModelViewSet):
    queryset = WorkerBio.objects.all()
    permission_classes = [permissions.IsAuthenticated , IsWorkerBioOrReadOnly]

    def perform_create(self, serializer):
        try:
            client_profile = self.request.user.client_profile
        except ObjectDoesNotExist:
            raise PermissionDenied("Client Profile does not exists ")
        if WorkerBio.objects.filter(client_profile = client_profile).exists():
            raise ValidationError("Worker Bio already exist")
        serializer.save(client_profile=client_profile)

    def get_serializer_class(self):
        if self.action in ['create' , 'update' , 'partial_update']:
            return WorkerBioOwnerSerializer
        return  WorkerBioPublicSerializer


class WorkerServiceView(viewsets.ModelViewSet):
    queryset = WorkerService.objects.select_related('worker__client_profile__user')
    serializer_class = WorkerServiceSerializer
    permission_classes = [permissions.IsAuthenticated,IsWorkerServiceOrReadOnly]

    def perform_create(self, serializer):
        try:
            worker = self.request.user.client_profile.worker_bio
        except ObjectDoesNotExist:
            raise PermissionDenied("Only workers can create services. Create your worker bio first.")
        serializer.save(worker=worker)
