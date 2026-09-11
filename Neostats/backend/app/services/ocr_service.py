import io
import os
from pypdf import PdfReader
from PIL import Image
from typing import List, Dict, Any
from backend.app.core.logging import logger

class OCRService:
    """
    Extracts text from PDF and Image documents, retaining page markers and line numbers
    to support source evidence/grounding (Section 4.3).
    """

    @staticmethod
    def extract_text(file_name: str, content: bytes) -> List[Dict[str, Any]]:
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ""
        pages_text = []

        if ext == 'pdf':
            try:
                reader = PdfReader(io.BytesIO(content))
                for idx, page in enumerate(reader.pages):
                    raw_text = page.extract_text() or ""
                    if not raw_text.strip():
                        raw_text = OCRService._ocr_pdf_page(content, idx)
                    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                    pages_text.append({
                        "page_number": idx + 1,
                        "text": raw_text,
                        "lines": lines
                    })
            except Exception as e:
                logger.error(f"PDF extraction error: {e}")
                
        elif ext in ['jpg', 'jpeg', 'png']:
            text_decoded = ""
            try:
                import pytesseract
                tesseract_path = os.getenv(
                    "TESSERACT_CMD",
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                )
                if os.path.exists(tesseract_path):
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                with Image.open(io.BytesIO(content)) as image:
                    candidates = [
                        pytesseract.image_to_string(image.rotate(angle, expand=True))
                        for angle in (0, 90, 180, 270)
                    ]
                    text_decoded = max(candidates, key=len)
            except (ImportError, OSError) as e:
                logger.error(f"Image OCR error for {file_name}: {e}")
        elif ext == 'txt':
            text_decoded = content.decode('utf-8', errors='ignore')

        if ext in ['jpg', 'jpeg', 'png', 'txt']:
            lines = [line.strip() for line in text_decoded.split('\n') if line.strip()]
            pages_text.append({
                "page_number": 1,
                "text": text_decoded,
                "lines": lines
            })

        return pages_text

    @staticmethod
    def _ocr_pdf_page(content: bytes, page_number: int) -> str:
        try:
            import fitz
            import pytesseract
            tesseract_path = os.getenv(
                "TESSERACT_CMD",
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            )
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            with fitz.open(stream=content, filetype="pdf") as document:
                page = document.load_page(page_number)
                image = Image.open(io.BytesIO(page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png")))
                grayscale = image.convert("L")
                candidates = [
                    pytesseract.image_to_string(image, config="--psm 6"),
                    pytesseract.image_to_string(image, config="--psm 11"),
                    pytesseract.image_to_string(grayscale, config="--psm 6"),
                    pytesseract.image_to_string(grayscale, config="--psm 11"),
                ]
                keywords = (
                    "total", "assets", "liabilities", "cash", "operating",
                    "investing", "financing", "profit", "income", "capital",
                )
                return max(
                    candidates,
                    key=lambda text: len(text) + 250 * sum(
                        keyword in text.lower() for keyword in keywords
                    ),
                )
        except (ImportError, OSError) as e:
            logger.error(f"Scanned PDF OCR error on page {page_number + 1}: {e}")
            return ""
