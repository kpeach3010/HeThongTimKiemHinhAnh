from rest_framework import serializers
from backend.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = '__all__'
        extra_kwargs = {
            'vip': {'read_only': True}
        }

