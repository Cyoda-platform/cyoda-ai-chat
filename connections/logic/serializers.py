from rest_framework import serializers

class InitialConnectionSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=255)
    ds_doc = serializers.CharField(max_length=255)

class ChatConnectionSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=255)
    user_endpoint = serializers.CharField(max_length=255, required=False)
    return_object = serializers.CharField(max_length=255)
    question = serializers.CharField(max_length=255)