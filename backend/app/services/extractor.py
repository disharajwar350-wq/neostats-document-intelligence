import io
from dataclasses import dataclass

import fitz
from PIL import Image


@dataclass
class ExtractionResult:
    text: str
    pages: list[str]
    ocr_used: bool


def extract_text(content: bytes, extension: str) -> ExtractionResult:
    if extension == ".pdf":
        return _extract_pdf(content)
    return _extract_image(content)


def _extract_pdf(content: bytes) -> ExtractionResult:
    pages: list[str] = []
    ocr_used = False
    with fitz.open(stream=content, filetype="pdf") as document:
        for page in document:
            text = page.get_text("text").strip()
            if not text:
                text = _ocr_image(page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png"))
                ocr_used = True
            pages.append(text)
    return ExtractionResult("\n\n".join(pages), pages, ocr_used)


def _extract_image(content: bytes) -> ExtractionResult:
    text = _ocr_image(content)
    return ExtractionResult(text, [text], True)


def _ocr_image(content: bytes) -> str:
    try:
        import pytesseract
        return pytesseract.image_to_string(Image.open(io.BytesIO(content))).strip()
    except (ImportError, OSError):
        return ""

