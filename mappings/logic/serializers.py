from rest_framework import serializers


# Custom serializers
class InitialMappingSerializer(serializers.Serializer):
    """Serializer for the initial mapping data."""

    id = serializers.CharField(max_length=255, required=True)
    entity = serializers.CharField(required=True)
    input = serializers.CharField(required=True)


class ChatMappingSerializer(serializers.Serializer):
    """Serializer for the chat mapping data."""

    id = serializers.CharField(max_length=255, required=True)
    question = serializers.CharField(required=True)
    user_script = serializers.CharField(required=False)
    return_object = serializers.CharField(max_length=255, required=True)
