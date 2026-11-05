from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from Client.models import PRICE_UNIT_CHOICES
from .models import ACTIVE_DEAL_STATUSES, Deal, Offer


VALID_PRICE_UNITS = {choice[0] for choice in PRICE_UNIT_CHOICES}


def get_actor_role(deal: Deal, user) -> str:
    """
    Rule #8: Verify that `user` is one of the two parties in `deal` and return
    their role ('client' or 'worker') in this specific deal.
    """
    if not user or not user.is_authenticated:
        raise ValidationError("Authentication is required.")

    try:
        client_profile = user.client_profile
    except ObjectDoesNotExist:
        raise ValidationError("User does not have a client profile.")

    if deal.client_id == client_profile.id:
        return 'client'

    try:
        worker_bio = client_profile.worker_bio
    except ObjectDoesNotExist:
        worker_bio = None

    if worker_bio is not None and deal.worker_id == worker_bio.id:
        return 'worker'

    raise ValidationError("Only the two parties of this deal can view or act on it.")


def _validate_price_and_unit(price, price_unit: str):
    """Ensure offer price is positive and price_unit is one of PRICE_UNIT_CHOICES."""
    if price is None or Decimal(str(price)) <= Decimal('0'):
        raise ValidationError({"price": "Offer price must be greater than zero."})
    if price_unit not in VALID_PRICE_UNITS:
        raise ValidationError({"price_unit": f"Invalid price unit '{price_unit}'."})


@transaction.atomic
def create_deal(
    *,
    user,
    job_post=None,
    worker_service=None,
    price,
    price_unit: str,
    message: str = '',
) -> Deal:
    """
    Creates a new Deal and its first pending Offer inside a single DB transaction.
      - Path A (job_post provided): caller must be a Worker applying to an open JobPost.
      - Path B (worker_service provided): caller is a Client requesting an available WorkerService.
    """
    # Enforce XOR: must come from either Path A or Path B, never both or neither.
    if (job_post is None) == (worker_service is None):
        raise ValidationError("Provide exactly one of 'job_post' or 'worker_service'.")

    _validate_price_and_unit(price, price_unit)

    try:
        caller_client_profile = user.client_profile
    except ObjectDoesNotExist:
        raise ValidationError("User does not have a client profile.")

    if job_post is not None:
        # Path A: Worker applies to a Client's JobPost.
        try:
            worker = caller_client_profile.worker_bio
        except ObjectDoesNotExist:
            raise ValidationError("Only users with a worker bio can apply to a job post.")

        if job_post.status != 'open':
            raise ValidationError("This job post is not open for applications.")

        client = job_post.client
        initiated_by = 'worker'

        # Rule #5: Prevent a user from applying to their own job post.
        if client.id == worker.client_profile_id:
            raise ValidationError("You cannot create a deal with yourself.")

        # Rule #4: Only one active deal per (job_post, worker).
        if Deal.objects.filter(
            job_post=job_post,
            worker=worker,
            status__in=ACTIVE_DEAL_STATUSES,
        ).exists():
            raise ValidationError("An active deal already exists for this job post and worker.")

    else:
        # Path B: Client sends a hire request for a Worker's WorkerService.
        if not worker_service.is_available:
            raise ValidationError("This worker service is currently unavailable.")

        client = caller_client_profile
        worker = worker_service.worker
        initiated_by = 'client'

        # Rule #5: Prevent a user from hiring their own worker service.
        if client.id == worker.client_profile_id:
            raise ValidationError("You cannot create a deal with yourself.")

        # Rule #4: Only one active deal per (worker_service, client).
        if Deal.objects.filter(
            worker_service=worker_service,
            client=client,
            status__in=ACTIVE_DEAL_STATUSES,
        ).exists():
            raise ValidationError("An active deal already exists for this worker service and client.")

    try:
        deal = Deal.objects.create(
            client=client,
            worker=worker,
            job_post=job_post,
            worker_service=worker_service,
            initiated_by=initiated_by,
            status='negotiating',
        )
        Offer.objects.create(
            deal=deal,
            sender=initiated_by,
            price=price,
            price_unit=price_unit,
            message=message or '',
            status='pending',
        )
    except IntegrityError as exc:
        raise ValidationError("Could not create deal due to a conflicting active deal.") from exc

    return deal


@transaction.atomic
def send_offer(
    *,
    deal: Deal,
    user,
    price,
    price_unit: str,
    message: str = '',
) -> Offer:
    """
    Sends a counter-offer on an existing negotiating Deal.
    Rule #2: Marks any existing pending offer on this Deal as 'superseded'.
    Rule #6: Disallowed once the deal leaves 'negotiating' status.
    """
    sender_role = get_actor_role(deal, user)

    # Rule #6: Price is locked once status is 'agreed' (or any non-negotiating state).
    if deal.status != 'negotiating':
        raise ValidationError(f"Cannot send offers when deal status is '{deal.status}'.")

    _validate_price_and_unit(price, price_unit)

    # Rule #2: Mark the previous pending offer as 'superseded' before inserting the new one
    # so the partial UniqueConstraint (unique_pending_offer_per_deal) is satisfied.
    deal.offers.filter(status='pending').update(status='superseded')

    offer = Offer.objects.create(
        deal=deal,
        sender=sender_role,
        price=price,
        price_unit=price_unit,
        message=message or '',
        status='pending',
    )
    # Touch deal.updated_at so recent activity sorts to the top.
    deal.save(update_fields=['updated_at'])
    return offer


@transaction.atomic
def accept_offer(*, deal: Deal, user) -> Deal:
    """
    Accepts the other party's latest pending offer on a Deal.
    Rule #1: Cannot accept your own offer; only the other party's pending offer can be accepted.
    Rule #3: Sets Deal.agreed_price, price_unit, status='agreed', agreed_at=now,
             and (for Path A) sets JobPost.status='assigned'.
    """
    actor_role = get_actor_role(deal, user)

    if deal.status != 'negotiating':
        raise ValidationError(f"Cannot accept an offer when deal status is '{deal.status}'.")

    pending_offer = deal.offers.filter(status='pending').order_by('-created_at', '-id').first()
    if pending_offer is None:
        raise ValidationError("There is no pending offer to accept on this deal.")

    # Rule #1: You cannot accept an offer that you sent yourself.
    if pending_offer.sender == actor_role:
        raise ValidationError("You cannot accept your own offer.")

    # Rule #3 (Path A): Assign the JobPost when the deal is agreed.
    if deal.job_post is not None:
        if deal.job_post.status != 'open':
            raise ValidationError("This job post is no longer open and cannot be assigned.")
        deal.job_post.status = 'assigned'
        deal.job_post.save(update_fields=['status', 'updated_at'])

    pending_offer.status = 'accepted'
    pending_offer.save(update_fields=['status'])

    deal.agreed_price = pending_offer.price
    deal.price_unit = pending_offer.price_unit
    deal.status = 'agreed'
    deal.agreed_at = timezone.now()
    deal.save(update_fields=['agreed_price', 'price_unit', 'status', 'agreed_at', 'updated_at'])

    return deal


@transaction.atomic
def decline_deal(*, deal: Deal, user) -> Deal:
    """
    Declines a Deal while it is still in 'negotiating' status.
    Marks any pending offer as 'declined' and sets Deal.status='declined'.
    """
    get_actor_role(deal, user)

    if deal.status != 'negotiating':
        raise ValidationError(
            f"Only a negotiating deal can be declined (current status: '{deal.status}')."
        )

    deal.offers.filter(status='pending').update(status='declined')
    deal.status = 'declined'
    deal.save(update_fields=['status', 'updated_at'])
    return deal


@transaction.atomic
def cancel_deal(*, deal: Deal, user) -> Deal:
    """
    Rule #7: Either party can cancel a deal before it is completed.
    If the deal was for a JobPost that had already been 'assigned', cancelling
    reopens the JobPost (status='open') so the client can hire someone else.
    """
    get_actor_role(deal, user)

    if deal.status not in ['negotiating', 'agreed', 'in_progress']:
        raise ValidationError(f"Cannot cancel a deal with status '{deal.status}'.")

    was_assigned = deal.status in ['agreed', 'in_progress']

    deal.offers.filter(status='pending').update(status='declined')
    deal.status = 'cancelled'
    deal.save(update_fields=['status', 'updated_at'])

    # Rule #7: Reopen the JobPost if an assigned deal gets cancelled.
    if was_assigned and deal.job_post is not None and deal.job_post.status == 'assigned':
        deal.job_post.status = 'open'
        deal.job_post.save(update_fields=['status', 'updated_at'])

    return deal


@transaction.atomic
def complete_deal(*, deal: Deal, user) -> Deal:
    """
    Rule #7: Only the client can mark an agreed/in-progress deal as completed.
    For Path A, also marks the linked JobPost as 'completed'.
    """
    actor_role = get_actor_role(deal, user)

    if actor_role != 'client':
        raise ValidationError("Only the client can mark a deal as completed.")

    if deal.status not in ['agreed', 'in_progress']:
        raise ValidationError(
            f"Only an agreed or in-progress deal can be completed (current status: '{deal.status}')."
        )

    deal.status = 'completed'
    deal.completed_at = timezone.now()
    deal.save(update_fields=['status', 'completed_at', 'updated_at'])

    if deal.job_post is not None and deal.job_post.status == 'assigned':
        deal.job_post.status = 'completed'
        deal.job_post.save(update_fields=['status', 'updated_at'])

    return deal
