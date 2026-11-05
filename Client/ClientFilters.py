

import django_filters
from .models import JobPost


class JobPostFilters(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name='city' , lookup_expr='iexact')
    area = django_filters.CharFilter(field_name='area' , lookup_expr='iexact')

    class Meta:
        model = JobPost
        fields = ['category'  , 'status']