"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

from Client.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('Client/', include('Client.urls')),
    path('api-token-auth/', LoginView.as_view(), name='login'),
    path('worker/', include('worker.urls')),
]