from decimal import Decimal
from rest_framework import serializers

from Client.models import JobPost, PRICE_UNIT_CHOICES
from worker.models import WorkerService
from .models import Deal, Offer


class OfferSerializer(serializers.ModelSerializer):
    """Read-only representation of an Offer inside a Deal."""

    class Meta:
        model = Offer
        fields = [
            'id',
            'deal',
            'sender',
            'price',
            'price_unit',
            'message',
            'status',
            'created_at',
        ]
        read_only_fields = fields


class OfferCreateSerializer(serializers.Serializer):
    """Validates input payload when sending a counter-offer on an existing Deal."""

    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
    )
    price_unit = serializers.ChoiceField(choices=PRICE_UNIT_CHOICES)
    message = serializers.CharField(required=False, allow_blank=True, default='')


class DealCreateSerializer(serializers.Serializer):
    """
    Validates input payload when starting a new Deal (Path A or Path B)
    along with its opening Offer.
    """

    job_post = serializers.PrimaryKeyRelatedField(
        queryset=JobPost.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )
    worker_service = serializers.PrimaryKeyRelatedField(
        queryset=WorkerService.objects.all(),
        required=False,
        allow_null=True,
        default=None,
    )
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
    )
    price_unit = serializers.ChoiceField(choices=PRICE_UNIT_CHOICES)
    message = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        # Object-level check: caller must supply either job_post (Path A) OR worker_service (Path B).
        has_job = attrs.get('job_post') is not None
        has_service = attrs.get('worker_service') is not None
        if has_job == has_service:
            raise serializers.ValidationError(
                "Provide exactly one of 'job_post' or 'worker_service'."
            )
        return attrs


class DealSerializer(serializers.ModelSerializer):
    """Full representation of a Deal, including nested Offer history and party usernames."""

    client_username = serializers.CharField(source='client.user.username', read_only=True)
    worker_username = serializers.CharField(
        source='worker.client_profile.user.username',
        read_only=True,
    )
    job_title = serializers.CharField(source='job_post.title', read_only=True, default=None)
    service_category = serializers.CharField(
        source='worker_service.category',
        read_only=True,
        default=None,
    )
    offers = OfferSerializer(many=True, read_only=True)

    class Meta:
        model = Deal
        fields = [
            'id',
            'client',
            'client_username',
            'worker',
            'worker_username',
            'job_post',
            'job_title',
            'worker_service',
            'service_category',
            'initiated_by',
            'status',
            'agreed_price',
            'price_unit',
            'agreed_at',
            'completed_at',
            'offers',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
