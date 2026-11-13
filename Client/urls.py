from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import ClientRegistrationView, PostjobView, MeView, LoginView, LogoutView

router = DefaultRouter()
router.register('jobs', PostjobView, basename='jobpost')

urlpatterns = [
    path('registration/', ClientRegistrationView.as_view(), name='registration'),
    path('me/', MeView.as_view(), name='me'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include(router.urls)),
]