from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import ClientProfile, JobPost


class ClientProfileSerializer(serializers.ModelSerializer):
    """Registration: creates a User and its ClientProfile in one request."""

    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = ClientProfile
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'phone_number', 'profile_picture', 'average_rating',
        ]
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
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        client_profile = ClientProfile.objects.create(user=user, **validated_data)
        return client_profile


class PostjobSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(source = 'client.user.username' , read_only=True)
    client_picture = serializers.ImageField(source = 'client.profile_picture',read_only=True)
    client_rating = serializers.DecimalField(source = 'client.average_rating',read_only=True,max_digits=3,decimal_places=2)
    class Meta:
        model = JobPost
        fields = [
            'id', 'client', 'client_username', 'client_picture', 'client_rating',
            'job_description', 'city', 'area', 'category',
            'price', 'duration', 'start_date', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['client', 'created_at', 'updated_at']


class MeSerializer(serializers.ModelSerializer):
    """The logged-in user's own profile: fields from User + ClientProfile."""

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    worker_bio_id = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'profile_picture', 'average_rating', 'created_at','worker_bio_id'
        ]
        read_only_fields = ['average_rating', 'created_at']

    def validate_email(self, value):
        own_user = self.instance.user
        if User.objects.filter(email=value).exclude(pk=own_user.pk).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        user = instance.user
        for key, value in user_data.items():
            setattr(user, key, value)
        user.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        return instance

    def get_worker_bio_id(self,obj):
        try:
            worker_bio = obj.worker_bio
        except ObjectDoesNotExist:
            return None
        return worker_bio.id
