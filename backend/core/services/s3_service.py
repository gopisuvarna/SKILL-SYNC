"""AWS S3 service for document storage and pre-signed URLs."""
import uuid
from django.conf import settings
import boto3
from botocore.exceptions import ClientError


class S3Service:
    def __init__(self):
        cfg = settings.AWS_STORAGE_CONFIG
        self.client = boto3.client(
            's3',
            aws_access_key_id=cfg['ACCESS_KEY_ID'],
            aws_secret_access_key=cfg['SECRET_ACCESS_KEY'],
            region_name=cfg['REGION'],
            config=boto3.session.Config(signature_version=cfg.get('SIGNATURE_VERSION', 's3v4')),
        )
        self.bucket = cfg['BUCKET_NAME']
        self.expiration = cfg.get('EXPIRATION', 3600)

    def generate_presigned_upload_url(self, user_id: str, filename: str, content_type: str) -> tuple[str, str]:
        """
        Generate pre-signed URL for PUT upload. Returns (upload_url, object_key).
        """
        ext = filename.rsplit('.', 1)[-1] if '.' in filename else 'pdf'
        object_key = f"documents/{user_id}/{uuid.uuid4().hex}.{ext}"
        params = {'Bucket': self.bucket, 'Key': object_key, 'ContentType': content_type}
        url = self.client.generate_presigned_url('put_object', Params=params, ExpiresIn=self.expiration)
        return url, object_key

    def generate_presigned_download_url(self, object_key: str) -> str:
        params = {'Bucket': self.bucket, 'Key': object_key}
        return self.client.generate_presigned_url('get_object', Params=params, ExpiresIn=self.expiration)

    def get_object_url(self, object_key: str) -> str:
        """Return permanent URL (or pre-signed if private bucket)."""
        return f"https://{self.bucket}.s3.amazonaws.com/{object_key}"
