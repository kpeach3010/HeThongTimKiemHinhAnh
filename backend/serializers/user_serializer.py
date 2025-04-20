from rest_framework import serializers
from backend.models import User


class UserSerializer(serializers.ModelSerializer):
    vip = serializers.SerializerMethodField()  # Lấy từ UserProfile

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'password', 'vip', 'is_superuser', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}  # Ẩn password khi trả về response
        }

    def get_vip(self, obj):
        """Lấy giá trị is_vip từ UserProfile"""
        return getattr(obj, "userprofile", None) and obj.userprofile.vip

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user
