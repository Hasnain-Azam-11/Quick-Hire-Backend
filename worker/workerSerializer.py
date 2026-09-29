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
    class Meta:
        model = WorkerService
        fields = [
            'id', 'category', 'job_description', 'city', 'area', 'rate',
            'is_available', 'created_at', 'updated_at',
        ]

        read_only_fields = ['created_at', 'updated_at']