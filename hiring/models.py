from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models

from Client.models import ClientProfile, JobPost, PRICE_UNIT_CHOICES
from worker.models import WorkerBio, WorkerService


PARTY_CHOICES = [
    ('client', 'Client'),
    ('worker', 'Worker'),
]

DEAL_STATUS_CHOICES = [
    ('negotiating', 'Negotiating'),
    ('agreed', 'Agreed'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('declined', 'Declined'),
    ('cancelled', 'Cancelled'),
    ('expired', 'Expired'),
]

# Statuses where a deal is still considered "active" (blocks duplicate active deals).
ACTIVE_DEAL_STATUSES = ['negotiating', 'agreed', 'in_progress']

OFFER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('superseded', 'Superseded'),
    ('declined', 'Declined'),
]


class Deal(models.Model):
    """
    Represents a hiring negotiation and agreement between a ClientProfile and a WorkerBio.
    Two entry paths feed into this single model:
      - Path A (Job Application): job_post is set, worker_service is None, initiated_by='worker'
      - Path B (Service Hire Request): worker_service is set, job_post is None, initiated_by='client'
    """

    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name='deals_as_client',
    )
    worker = models.ForeignKey(
        WorkerBio,
        on_delete=models.CASCADE,
        related_name='deals_as_worker',
    )

    # Nullable FKs because a Deal comes from EITHER a JobPost (Path A) OR a WorkerService (Path B).
    job_post = models.ForeignKey(
        JobPost,
        on_delete=models.CASCADE,
        related_name='deals',
        null=True,
        blank=True,
    )
    worker_service = models.ForeignKey(
        WorkerService,
        on_delete=models.CASCADE,
        related_name='deals',
        null=True,
        blank=True,
    )

    initiated_by = models.CharField(max_length=10, choices=PARTY_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=DEAL_STATUS_CHOICES,
        default='negotiating',
    )

    # Locked in only when one party accepts the other's pending Offer (Rule #3 & #6).
    agreed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    price_unit = models.CharField(
        max_length=10,
        choices=PRICE_UNIT_CHOICES,
        null=True,
        blank=True,
    )

    agreed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # Enforce XOR at DB level: exactly one of job_post or worker_service must be set.
            models.CheckConstraint(
                condition=(
                    models.Q(job_post__isnull=False, worker_service__isnull=True)
                    | models.Q(job_post__isnull=True, worker_service__isnull=False)
                ),
                name='deal_must_have_exactly_one_source',
            ),
            # Rule #4 (Path A): Only one active deal per (job_post, worker).
            # If a previous deal was declined/cancelled, they can start a new one later.
            models.UniqueConstraint(
                fields=['job_post', 'worker'],
                condition=models.Q(
                    job_post__isnull=False,
                    status__in=ACTIVE_DEAL_STATUSES,
                ),
                name='unique_active_deal_per_job_and_worker',
            ),
            # Rule #4 (Path B): Only one active deal per (worker_service, client).
            models.UniqueConstraint(
                fields=['worker_service', 'client'],
                condition=models.Q(
                    worker_service__isnull=False,
                    status__in=ACTIVE_DEAL_STATUSES,
                ),
                name='unique_active_deal_per_service_and_client',
            ),
        ]

    def __str__(self):
        source = f"Job #{self.job_post_id}" if self.job_post_id else f"Service #{self.worker_service_id}"
        return f"Deal #{self.id} ({source}) - {self.status}"


class Offer(models.Model):
    """
    A price quote or counter-offer inside a Deal.
    Only one Offer per Deal can be 'pending' at a time; sending a new Offer marks
    the previous pending Offer as 'superseded' (Rule #2).
    """

    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='offers',
    )
    sender = models.CharField(max_length=10, choices=PARTY_CHOICES)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    price_unit = models.CharField(max_length=10, choices=PRICE_UNIT_CHOICES)
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=OFFER_STATUS_CHOICES,
        default='pending',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Chronological order so offers read like a conversation history from oldest to newest.
        ordering = ['created_at', 'id']
        constraints = [
            # Rule #2: At most one pending offer can exist per deal at any moment.
            models.UniqueConstraint(
                fields=['deal'],
                condition=models.Q(status='pending'),
                name='unique_pending_offer_per_deal',
            ),
            models.CheckConstraint(
                condition=models.Q(price__gt=0),
                name='offer_price_must_be_positive',
            ),
        ]

    def __str__(self):
        return f"Offer #{self.id} on Deal #{self.deal_id} by {self.sender}: {self.price}/{self.price_unit} ({self.status})"
