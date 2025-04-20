from rest_framework import serializers


class SearchByTextSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500)
    top_k = serializers.IntegerField(min_value=1, default=8)


class SearchByImageSerializer(serializers.Serializer):
    image = serializers.ImageField()
    top_k = serializers.IntegerField(min_value=1, default=8)


class UploadImageSerializer(serializers.Serializer):
    image = serializers.ImageField()
