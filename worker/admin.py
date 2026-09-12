from django.contrib import admin
from .models import WorkerService,WorkerBio
# Register your models here.
admin.site.register(WorkerBio),
admin.site.register(WorkerService)
