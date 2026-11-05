from django.db import models
from django.contrib.auth.models import User

CATEGORY_CHOICES = [
    ('driving', 'Driving'),
    ('moving', 'Moving'),
    ('handyman', 'Handyman'),
    ('caregiving', 'Care Giving'),
    ('event_staffing', 'Event Staffing'),
    ('cooking', 'Cooking'),
    ('construction', 'Construction'),
    ('security', 'Security'),
    ('gardening', 'Gardening'),
    ('tutoring', 'Tutoring'),
    ('beauty', 'Beauty'),
    ('cleaning', 'Cleaning'),
]

JOB_STATUS_CHOICES = [
    ('open', 'Open'),
    ('assigned', 'Assigned'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

# Shared time/billing unit choices used across JobPost (duration_unit),
# WorkerService (price_unit), and hiring Deals/Offers.
PRICE_UNIT_CHOICES = [
    ('hour', 'Per hour'),
    ('day', 'Per day'),
    ('week', 'Per week'),
    ('month', 'Per month'),
    ('flat', 'Flat (event / task / session)'),
]



class ClientProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='client_profiles/', blank=True, null=True)

    # Aggregate rating (will be recalculated from reviews once reviews exist)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} (Client)"


class JobPost(models.Model):

    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='job_posts')
    title = models.CharField(max_length=150)
    job_description = models.TextField()
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    # Client specifies the time unit needed (hour/day/week/month/flat) and duration,
    # while workers propose the actual price during deal negotiation.
    duration_unit = models.CharField(max_length=10, choices=PRICE_UNIT_CHOICES)
    duration = models.CharField(max_length=100, help_text="e.g. '2 hours', '3 days'")
    start_date = models.DateField()
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='open')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.client.user.username} - {self.city}"