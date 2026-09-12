from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ClientProfile, JobPost


class ClientProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = ClientProfile
        fields = ['id', 'phone_number', 'username', 'email', 'password', 'profile_picture', 'average_rating']
        read_only_fields = ['average_rating']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        client_profile = ClientProfile.objects.create(user=user, **validated_data)
        return client_profile


class PostjobSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = [
            'id', 'client', 'job_description', 'city', 'area', 'category',
            'price', 'duration', 'start_date', 'status',
            'created_at', 'updated_at',
        ]
        # 'client' set automatically in the view from request.user - never
        # trust it from client input, or anyone could post a job "as"
        # someone else.
        read_only_fields = ['client', 'created_at', 'updated_at']

    # No custom create() needed - ModelSerializer's default create() already
    # does `JobPost.objects.create(**validated_data)` for us.