from rest_framework import serializers

# Custom serializers
class InitialMappingSerializer(serializers.Serializer):
    """Serializer for the initial mapping data."""
    id = serializers.CharField(max_length=255)
    entity = serializers.CharField(max_length=255)
    input = serializers.CharField(max_length=255)

class ChatMappingSerializer(serializers.Serializer):
    """Serializer for the chat mapping data."""
    id = serializers.CharField(max_length=255)
    question = serializers.CharField(max_length=255)
    user_script = serializers.CharField(max_length=255)
    return_object = serializers.CharField(max_length=255)