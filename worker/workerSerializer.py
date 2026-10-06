from rest_framework import serializers
from .models import WorkerBio, WorkerService


class WorkerBioOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerBio
        fields = [
            'id', 'cnic', 'age', 'years_of_experience', 'expertise_categories',
            'gender', 'bio', 'is_verified', 'average_rating',
            'created_at', 'updated_at',
        ]

        read_only_fields = ['is_verified', 'average_rating', 'created_at', 'updated_at']

class WorkerBioPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerBio
        fields = [
            'id', 'age', 'years_of_experience', 'expertise_categories',
            'gender', 'bio', 'is_verified', 'average_rating',
            'created_at', 'updated_at',
        ]

        read_only_fields = ['is_verified', 'average_rating', 'created_at', 'updated_at']


class WorkerServiceSerializer(serializers.ModelSerializer):
    worker_username = serializers.CharField(source='worker.client_profile.user.username' ,read_only=True)
    worker_picture = serializers.ImageField(source = 'worker.client_profile.profile_picture',read_only=True)
    worker_is_verified =  serializers.BooleanField(source = 'worker.is_verified',read_only=True)
    worker_average_rating = serializers.DecimalField(source = 'worker.average_rating',max_digits=3, decimal_places=2,read_only=True)
    worker_years_of_experience = serializers.IntegerField(source='worker.years_of_experience',read_only=True)
    class Meta:
        model = WorkerService
        fields = [
            'id', 'worker','category', 'job_description', 'city', 'area', 'rate',
            'is_available', 'created_at', 'updated_at', 'worker_username' , 'worker_picture','worker_is_verified' ,
            'worker_average_rating' , 'worker_years_of_experience'
        ]

        read_only_fields = ['worker','created_at', 'updated_at']