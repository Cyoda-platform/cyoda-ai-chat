from rest_framework import serializers

class MessageSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    question = serializers.CharField(required=False)
    ds_doc = serializers.CharField(required=False)
    return_object = serializers.CharField(required=False)
    user_endpoint = serializers.CharField(required=False)  # Make this field optional