from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

CATEGORY_CHOICES = [
        ('Driving', 'Driving'),
        ('Moving', 'Moving'),
        ('Handyman', 'Handyman'),
        ('Childcare', 'Childcare'),
        ('Elder Care', 'Elder Care'),
        ('Event Staffing', 'Event Staffing'),
        ('Cooking', 'Cooking'),
        ('Construction', 'Construction'),
        ('Security', 'Security'),
        ('Gardening', 'Gardening'),
        ('Tutoring', 'Tutoring'),
        ('Beauty', 'Beauty'),
    ]

JOB_STATUS_CHOICES = [
    ('open', 'Open'),
    ('assigned', 'Assigned'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


class ClientProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='client_profiles/', blank=True, null=True)

    # Aggregate rating (auto-updated whenever a new WorkerReviewOnClient is added)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} (Client)"


class JobPost(models.Model):

    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name='job_posts')
    job_description = models.TextField()
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fair/price offered by client")
    duration = models.CharField(max_length=100, help_text="e.g. '2 hours', '3 days'")
    start_date = models.DateField()
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default='open')



    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category} job by {self.client.user.username} - {self.city}"


class Category(models.Model):
    """
    A real model (not just a choices list) - needed because WorkerBio uses a
    ManyToMany relationship (a worker can be expert in multiple categories),
    and M2M only works against an actual model, not a CharField choices list.

    JobPost and WorkerService still use CATEGORY_CHOICES as a simple CharField
    (a job/service belongs to exactly ONE category), so this doesn't replace
    that - it's specifically for the multi-category expertise case.
    """
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
