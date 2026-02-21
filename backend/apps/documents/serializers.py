"""Document serializers."""
from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'file_url', 'uploaded_at', 'parsed')
        read_only_fields = fields


class PresignedUploadRequestSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(default='application/pdf', max_length=100)
