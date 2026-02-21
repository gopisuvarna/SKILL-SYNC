"""Signals to trigger PDF parsing after document upload."""
import os
import tempfile
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Document
from core.services.document_parser import DocumentParserService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def parse_document_on_save(sender, instance: Document, created: bool, **kwargs):
    if not created or instance.parsed:
        return
    # Deferred: in production, use Celery/RQ to parse asynchronously.
    # Here we simulate async by parsing in signal (blocking). For real async, enqueue task.
    try:
        from core.services.s3_service import S3Service
        s3 = S3Service()
        # Download to temp file and parse
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            try:
                s3.client.download_fileobj(s3.bucket, instance.s3_key, tmp)
                tmp_path = tmp.name
            except Exception as e:
                logger.warning("S3 download failed: %s", e)
                return
        try:
            parser = DocumentParserService()
            text = parser.parse_pdf(tmp_path)
            if text:
                Document.objects.filter(pk=instance.pk).update(extracted_text=text, parsed=True)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    except Exception as e:
        logger.exception("Parse failed: %s", e)
