from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import WorkerBioView, WorkerServiceView,PublicWorkerListingView

router = DefaultRouter()
router.register('workerBio', WorkerBioView, basename='workerBio')
router.register('workerService', WorkerServiceView, basename='workerService')

urlpatterns = [
    path('', include(router.urls)),
    path('browseworkers/',PublicWorkerListingView.as_view(),name='browseworkers')
]
