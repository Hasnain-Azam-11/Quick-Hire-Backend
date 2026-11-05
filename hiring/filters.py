import django_filters
from .models import Deal


class DealFilter(django_filters.FilterSet):
    """
    Filters "my deals" by:
      - ?role=client  -> deals where the logged-in user is the client
      - ?role=worker  -> deals where the logged-in user is the worker
      - ?status=...   -> deals in a given status (negotiating, agreed, completed, etc.)
      - ?job_post=... / ?worker_service=...
    """

    role = django_filters.ChoiceFilter(
        choices=[('client', 'Client'), ('worker', 'Worker')],
        method='filter_by_role',
    )

    class Meta:
        model = Deal
        fields = ['status', 'job_post', 'worker_service', 'initiated_by']

    def filter_by_role(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return queryset.none()
        if value == 'client':
            return queryset.filter(client__user=user)
        if value == 'worker':
            return queryset.filter(worker__client_profile__user=user)
        return queryset
