"""Document upload and management views."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.services.s3_service import S3Service
from core.services.document_parser import DocumentParserService
from .models import Document
from .serializers import DocumentSerializer, PresignedUploadRequestSerializer


ALLOWED_CONTENT_TYPES = ('application/pdf',)
ALLOWED_EXTENSIONS = ('pdf',)
MAX_FILENAME_LEN = 255


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_presigned_upload_url(request):
    """Return pre-signed URL for direct S3 upload."""
    serializer = PresignedUploadRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    filename = serializer.validated_data['filename']
    content_type = serializer.validated_data['content_type']
    if content_type not in ALLOWED_CONTENT_TYPES:
        return Response({'detail': 'Only PDF files allowed'}, status=status.HTTP_400_BAD_REQUEST)
    if len(filename) > MAX_FILENAME_LEN:
        return Response({'detail': 'Filename too long'}, status=status.HTTP_400_BAD_REQUEST)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return Response({'detail': 'Invalid file extension'}, status=status.HTTP_400_BAD_REQUEST)

    s3 = S3Service()
    upload_url, object_key = s3.generate_presigned_upload_url(
        str(request.user.id), filename, content_type
    )
    return Response({'upload_url': upload_url, 'object_key': object_key})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_upload(request):
    """Create Document record after client has uploaded to S3."""
    object_key = request.data.get('object_key')
    if not object_key or not isinstance(object_key, str):
        return Response({'detail': 'object_key required'}, status=status.HTTP_400_BAD_REQUEST)
    if not object_key.startswith(f'documents/{request.user.id}/'):
        return Response({'detail': 'Invalid object_key'}, status=status.HTTP_403_FORBIDDEN)

    s3 = S3Service()
    file_url = s3.get_object_url(object_key)
    doc = Document.objects.create(user=request.user, file_url=file_url, s3_key=object_key)
    return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_documents(request):
    docs = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    return Response(DocumentSerializer(docs, many=True).data)
