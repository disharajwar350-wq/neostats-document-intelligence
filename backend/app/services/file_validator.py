from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image


SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
SUPPORTED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}
MAX_PAGES = 3


@dataclass
class ValidatedFile:
    extension: str
    mime_type: str
    page_count: int
    is_readable: bool
    error_code: str | None = None
    message: str | None = None


def validate_file(filename: str, content: bytes) -> ValidatedFile:
    extension = Path(filename or "").suffix.lower()
    mime_type = SUPPORTED_MIME_TYPES.get(extension, "application/octet-stream")

    if extension not in SUPPORTED_EXTENSIONS:
        return ValidatedFile(extension, mime_type, 0, False, "UNSUPPORTED_FILE_TYPE",
                              "Only PDF, JPG and PNG documents are supported.")
    if not content:
        return ValidatedFile(extension, mime_type, 0, False, "EMPTY_FILE",
                              "The uploaded file is empty.")

    try:
        if extension == ".pdf":
            with fitz.open(stream=content, filetype="pdf") as document:
                page_count = document.page_count
                if page_count == 0:
                    raise ValueError("The PDF contains no pages.")
                if page_count > MAX_PAGES:
                    return ValidatedFile(extension, mime_type, page_count, False,
                                         "PAGE_LIMIT_EXCEEDED",
                                         "Documents may contain no more than 3 pages.")
        else:
            with Image.open(__import__("io").BytesIO(content)) as image:
                image.verify()
            page_count = 1
        return ValidatedFile(extension, mime_type, page_count, True)
    except Exception:
        return ValidatedFile(extension, mime_type, 0, False, "UNREADABLE_FILE",
                              "The uploaded file is corrupted or unreadable.")

