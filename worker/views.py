from rest_framework import generics,permissions,viewsets

# from Client import permissions, serializer
from .workerSerializer import WorkerbioSerializer,WorkerServiceSerializer
from .models import WorkerBio,WorkerService
from .workerPermissions import IsWorkerOrReadOnly
# Create your views here.
class WorkerBioView(viewsets.ModelViewSet):
    queryset = WorkerBio.objects.all()
    serializer_class = WorkerbioSerializer
    permission_classes = [permissions.IsAuthenticated , IsWorkerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(client_profile = self.request.client_profile)

class WorkerServiceView(viewsets.ModelViewSet):
    queryset = WorkerService.objects.all()
    serializer_class = WorkerServiceSerializer
    permissions_classes = [permissions.AllowAny,IsWorkerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(worker = self.request.worker)

