from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from Client.models import CATEGORY_CHOICES, ClientProfile, Category


GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]


class WorkerBio(models.Model):

    client_profile = models.OneToOneField(ClientProfile, on_delete=models.CASCADE, related_name='worker_bio')

    cnic = models.CharField(max_length=15, unique=True, help_text="Format: 12345-1234567-1")

    age = models.PositiveIntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(100)],
        help_text="Age must be between 18 and 100"
    )

    years_of_experience = models.PositiveIntegerField(default=0, help_text="Total years of experience")

    expertise_categories = models.ManyToManyField(
        Category, related_name='expert_workers',
        help_text="Categories worker is expert in"
    )

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    bio = models.TextField(blank=True, help_text="Short description about yourself")

    is_verified = models.BooleanField(default=False)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client_profile.user.username}'s Worker Bio"


class WorkerService(models.Model):

    worker = models.ForeignKey(WorkerBio, on_delete=models.CASCADE, related_name='services')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    job_description = models.TextField(help_text="Description of the service offered")
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Worker's own asking rate/price")
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category} service by {self.worker.client_profile.user.username} - {self.city}"