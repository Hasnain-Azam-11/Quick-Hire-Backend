from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phoneNumber = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.user.username


class WorkerProfile(models.Model):
    CATEGORY_CHOICES = [
        ('Childcare', 'Childcare'),
        ('Elder Care', 'Elder Care'),
        ('Event Staffing', 'Event Staffing'),
        ('Cooking', 'Cooking'),
        ('Driving', 'Driving'),
        ('Construction', 'Construction'),
        ('Security', 'Security'),
        ('Gardening', 'Gardening'),
        ('Tutoring', 'Tutoring'),
        ('Beauty', 'Beauty'),
        ('Handyman', 'Handyman'),
        ('Moving', 'Moving'),
        ('Office Support', 'Office Support'),
    ]

    client = models.OneToOneField(Client, on_delete=models.CASCADE)  # ✅ Spelling sahi, lowercase
    cnic = models.FileField(upload_to='cnic_docs/')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    years_of_experience = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.client.user.username} - {self.category}"  # ✅ self.client (not self.worker)