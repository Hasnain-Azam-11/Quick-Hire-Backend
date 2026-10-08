

import django_filters
from .models import WorkerService

class WorkerServiceFilter(django_filters.FilterSet):
    max_rate = django_filters.NumberFilter(field_name='rate',lookup_expr='lte')
    min_rate = django_filters.NumberFilter(field_name='rate',lookup_expr='gte')
    city = django_filters.CharFilter(field_name='city',lookup_expr='iexact')
    area = django_filters.CharFilter(field_name='area' , lookup_expr='iexact')
    class Meta:
        model = WorkerService
        fields = ['category','is_available']

