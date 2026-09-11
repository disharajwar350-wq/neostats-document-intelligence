import os
from pypdf import PdfReader
from PIL import Image
import io
from typing import Dict, Any, Tuple

from backend.app.core.config import settings
from backend.app.core.logging import logger

class DocumentValidationService:
    """
    Validates uploaded document files according to Section 3 & 4.1 requirements:
    - Supported formats: PDF, JPG, PNG
    - File integrity and readability
    - Page count <= 3
    - Rejects empty or corrupted files
    """

    @staticmethod
    def validate_file(file_name: str, content: bytes, content_type: str = "") -> Tuple[bool, Dict[str, Any]]:
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ""
        
        validation = {
            "file_type": content_type or f"application/{ext}",
            "is_supported": False,
            "is_readable": False,
            "page_count": 0,
            "status": "FAILED",
            "error_message": None
        }

        # 1. File extension & content type check
        if ext not in settings.ALLOWED_EXTENSIONS:
            validation["error_message"] = f"Unsupported file extension '.{ext}'. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            return False, validation

        validation["is_supported"] = True

        expected_mime_types = {
            "pdf": {"application/pdf"},
            "jpg": {"image/jpeg", "image/jpg"},
            "jpeg": {"image/jpeg", "image/jpg"},
            "png": {"image/png"},
        }
        normalized_content_type = content_type.lower()
        if content_type and normalized_content_type not in settings.ALLOWED_MIME_TYPES:
            validation["error_message"] = (
                f"Unsupported MIME type '{content_type}'. "
                "Supported: application/pdf, image/jpeg, image/png."
            )
            return False, validation
        if content_type and normalized_content_type not in expected_mime_types[ext]:
            validation["error_message"] = (
                f"MIME type '{content_type}' does not match the '.{ext}' extension."
            )
            return False, validation

        # 2. Empty file check
        if not content or len(content) == 0:
            validation["error_message"] = "File is empty (0 bytes)."
            return False, validation

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            validation["error_message"] = (
                f"File exceeds the maximum size of {settings.MAX_FILE_SIZE_MB} MB."
            )
            return False, validation

        # 3. Readability & page count check
        try:
            if ext == 'pdf':
                reader = PdfReader(io.BytesIO(content))
                page_count = len(reader.pages)
                validation["page_count"] = page_count
                validation["is_readable"] = True

                if page_count == 0:
                    validation["error_message"] = "PDF does not contain any pages."
                    return False, validation
                if page_count > settings.MAX_PAGE_COUNT:
                    validation["error_message"] = f"Document exceeds maximum page limit of {settings.MAX_PAGE_COUNT} pages (Found: {page_count})."
                    return False, validation

            elif ext in ['jpg', 'jpeg', 'png']:
                img = Image.open(io.BytesIO(content))
                img.verify()
                validation["page_count"] = 1
                validation["is_readable"] = True
            
            validation["status"] = "PASS"
            return True, validation

        except Exception as e:
            logger.error(f"File validation failed for {file_name}: {str(e)}")
            validation["is_readable"] = False
            validation["error_message"] = f"File is corrupted or unreadable: {str(e)}"
            return False, validation
