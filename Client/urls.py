from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientRegistrationView, PostjobView

router = DefaultRouter()
router.register('jobs', PostjobView, basename='jobpost')

urlpatterns = [
    path('registration/', ClientRegistrationView.as_view(), name='registration'),
    path('', include(router.urls)),
]