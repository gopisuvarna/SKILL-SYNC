"""PDF parsing service using PyMuPDF. Handles corrupted/empty/large documents."""
import logging
import re
from typing import Optional

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

MAX_PAGES = 500
MAX_CHARS_PER_PAGE = 50000


class DocumentParserService:
    def parse_pdf(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF. Returns None for corrupted/empty documents.
        Handles large documents by limiting pages and chars per page.
        """
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.warning("Failed to open PDF: %s", e)
            return None
        try:
            pages = min(len(doc), MAX_PAGES)
            if pages == 0:
                return None
            chunks = []
            total_chars = 0
            for i in range(pages):
                page = doc.load_page(i)
                text = page.get_text()
                if len(text) > MAX_CHARS_PER_PAGE:
                    text = text[:MAX_CHARS_PER_PAGE]
                text = self._clean_text(text)
                if text:
                    chunks.append(text)
                total_chars += len(text)
                if total_chars > 1_000_000:
                    break
            result = '\n\n'.join(chunks).strip()
            return result if result else None
        finally:
            doc.close()

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()
