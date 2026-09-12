from unicodedata import category

from rest_framework import serializers
from .models import WorkerBio , WorkerService


class WorkerbioSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerBio
        fields = [
            'cnic',
            'age',
            'years_of_experience',
            'expertise_categories',
            'gender',
            'bio',
            'is_verified',
            'average_rating',
        ]
        read_only_fields = ['updated_at', 'created_at']

class WorkerServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerService
        fields = ['category', 'job_description' , 'city' ,'area', 'is_avalable']
        read_only_fields = ['created_at' , 'updated_at']

