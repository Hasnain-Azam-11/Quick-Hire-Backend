from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .filters import DealFilter
from .models import Deal
from .permissions import IsDealParty
from .serializers import (
    DealCreateSerializer,
    DealSerializer,
    OfferCreateSerializer,
    OfferSerializer,
)


class DealViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Thin ViewSet for the Deal lifecycle.
    We intentionally omit UpdateModelMixin and DestroyModelMixin so clients cannot
    arbitrarily PUT/PATCH/DELETE a Deal; all state changes go through services.py.
    """

    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated, IsDealParty]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DealFilter

    def get_queryset(self):
        # Preload related objects in one query (select_related / prefetch_related)
        # to avoid the N+1 query problem when serializing deals and their offers.
        base_qs = Deal.objects.select_related(
            'client__user',
            'worker__client_profile__user',
            'job_post',
            'worker_service',
        ).prefetch_related('offers')

        # On list (`GET /hiring/deals/`), only return deals where the caller is a party.
        # On detail actions, `IsDealParty.has_object_permission` enforces 403 for outsiders.
        if self.action == 'list':
            user = self.request.user
            return base_qs.filter(
                Q(client__user=user) | Q(worker__client_profile__user=user)
            )
        return base_qs

    def get_serializer_class(self):
        if self.action == 'create':
            return DealCreateSerializer
        if self.action == 'offers':
            return OfferCreateSerializer
        return DealSerializer

    def create(self, request, *args, **kwargs):
        """POST /hiring/deals/ -> Start a new Deal (Path A or Path B) + opening Offer."""
        in_serializer = DealCreateSerializer(data=request.data)
        in_serializer.is_valid(raise_exception=True)

        deal = services.create_deal(
            user=request.user,
            job_post=in_serializer.validated_data.get('job_post'),
            worker_service=in_serializer.validated_data.get('worker_service'),
            price=in_serializer.validated_data['price'],
            price_unit=in_serializer.validated_data['price_unit'],
            message=in_serializer.validated_data.get('message', ''),
        )
        out_serializer = DealSerializer(deal, context={'request': request})
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='offers')
    def offers(self, request, pk=None):
        """POST /hiring/deals/<id>/offers/ -> Send a counter-offer on a negotiating Deal."""
        deal = self.get_object()
        in_serializer = OfferCreateSerializer(data=request.data)
        in_serializer.is_valid(raise_exception=True)

        offer = services.send_offer(
            deal=deal,
            user=request.user,
            price=in_serializer.validated_data['price'],
            price_unit=in_serializer.validated_data['price_unit'],
            message=in_serializer.validated_data.get('message', ''),
        )
        return Response(OfferSerializer(offer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='accept')
    def accept(self, request, pk=None):
        """POST /hiring/deals/<id>/accept/ -> Accept the other party's pending Offer."""
        deal = self.get_object()
        updated_deal = services.accept_offer(deal=deal, user=request.user)
        return Response(DealSerializer(updated_deal, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='decline')
    def decline(self, request, pk=None):
        """POST /hiring/deals/<id>/decline/ -> Decline a negotiating Deal."""
        deal = self.get_object()
        updated_deal = services.decline_deal(deal=deal, user=request.user)
        return Response(DealSerializer(updated_deal, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """POST /hiring/deals/<id>/cancel/ -> Cancel a Deal before completion."""
        deal = self.get_object()
        updated_deal = services.cancel_deal(deal=deal, user=request.user)
        return Response(DealSerializer(updated_deal, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """POST /hiring/deals/<id>/complete/ -> Client marks an agreed Deal as completed."""
        deal = self.get_object()
        updated_deal = services.complete_deal(deal=deal, user=request.user)
        return Response(DealSerializer(updated_deal, context={'request': request}).data)
