from Client.urls import urlpatterns,path
from .views import WorkerBioView , WorkerServiceView
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('workerBio',WorkerBioView,'workerBio')
router.register('workerService',WorkerServiceView, 'workerService')