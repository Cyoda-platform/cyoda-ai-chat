from rest_framework import serializers

class MessageSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    question = serializers.CharField(required=False)
    entity = serializers.CharField(required=False)
    input = serializers.CharField(required=False)
    return_object = serializers.CharField(required=False)
    user_script = serializers.CharField(required=False)
    content = serializers.CharField(required=False)  # Make this field optional