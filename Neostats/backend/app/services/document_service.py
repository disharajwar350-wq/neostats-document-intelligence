import time
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

from backend.app.services.document_validation_service import DocumentValidationService
from backend.app.services.ocr_service import OCRService
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.financial_validation_service import FinancialValidationService
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.core.logging import logger

class DocumentService:
    """
    Master business service orchestrating the document intelligence workflow.
    """

    @staticmethod
    def _confidence_report(extracted_data: Dict[str, Any], pages_text: list, validation: Dict[str, Any]) -> Dict[str, Any]:
        texts = [page.get("text", "") for page in pages_text]
        combined = "\n".join(texts)
        non_whitespace = [char for char in combined if not char.isspace()]
        printable_ratio = (
            sum(char.isprintable() for char in non_whitespace) / len(non_whitespace)
            if non_whitespace else 0.0
        )
        alphanumeric_ratio = (
            sum(char.isalnum() for char in non_whitespace) / len(non_whitespace)
            if non_whitespace else 0.0
        )
        source_quality = round((printable_ratio + alphanumeric_ratio) / 2, 4)

        field_scores = []
        for key, field in extracted_data.items():
            if key == "line_items" or not isinstance(field, dict):
                continue
            if field.get("value") is None:
                field["confidence"] = 0.0
                continue
            evidence = field.get("evidence") or {}
            source_text = str(evidence.get("source_text", "")).strip()
            evidence_score = 1.0 if source_text and evidence.get("page_number") else 0.0
            source_signal = min(len(source_text) / 80, 1.0)
            score = round(
                source_quality * 0.35
                + evidence_score * 0.45
                + source_signal * 0.20,
                4,
            )
            field["confidence"] = score
            field_scores.append(score)

        statuses = [check.get("status") for check in validation.get("checks", [])]
        validation_factor = (
            1.0 if statuses and all(status == "PASS" for status in statuses)
            else 0.96 if statuses and all(status in {"PASS", "PASS_WITH_TOLERANCE", "NOT_APPLICABLE"} for status in statuses)
            else 0.75 if statuses
            else 0.9
        )
        extraction_factor = (
            sum(field_scores) / len(field_scores)
            if field_scores else 0.0
        )
        overall = round(extraction_factor * validation_factor, 4)
        return {
            "overall": overall,
            "source_quality": source_quality,
            "validation_factor": validation_factor,
            "fields_scored": len(field_scores),
            "fields_with_evidence": sum(
                1 for key, field in extracted_data.items()
                if key != "line_items" and isinstance(field, dict) and field.get("evidence")
            ),
        }

    @staticmethod
    def process_document(file_name: str, content: bytes, document_type: str, content_type: str = "") -> Tuple[Dict[str, Any], int]:
        start_time = time.time()
        
        # 1. File Validation Layer (Section 4.1)
        is_valid, file_val_result = DocumentValidationService.validate_file(file_name, content, content_type)
        
        if not is_valid:
            error_response = {
                "error": {
                    "code": "INVALID_FILE_ERROR" if file_val_result.get("is_supported") else "UNSUPPORTED_FILE_TYPE",
                    "message": file_val_result.get("error_message") or "Document validation failed."
                }
            }
            return error_response, 400

        # 2. Text Extraction / OCR (Section 4.2)
        pages_text = OCRService.extract_text(file_name, content)
        if not any(page.get("text", "").strip() for page in pages_text):
            return {
                "error": {
                    "code": "EXTRACTION_FAILED",
                    "message": "No readable text could be extracted from the document."
                }
            }, 422

        # 3. Field & Table Extraction
        extracted_data = ExtractionService.extract(document_type, pages_text)

        # 4. Financial Calculation Validation (Section 4.4)
        validation_result = FinancialValidationService.validate_document(document_type, extracted_data)
        confidence = DocumentService._confidence_report(extracted_data, pages_text, validation_result)

        extracted_fields = [
            value for key, value in extracted_data.items()
            if key != "line_items" and isinstance(value, dict) and value.get("value") is not None
        ]
        proc_status = (
            "PASS"
            if extracted_fields and validation_result["overall_status"] != "FAIL"
            else "FAILED"
        )
        if not file_val_result["is_readable"]:
            proc_status = "FAILED"

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build response JSON matching Section 5.2 schema
        response = {
            "document_name": file_name,
            "document_type": document_type,
            "processing_status": proc_status,
            "overall_confidence": confidence["overall"],
            "file_validation": file_val_result,
            "extracted_data": extracted_data,
            "validation": validation_result,
            "processing_metadata": {
                "ocr_used": True,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "processing_time_ms": processing_time_ms
                ,
                "confidence_factors": confidence
            }
        }

        # 5. Database Persistence (Section 5.1)
        DocumentRepository.save_document(file_name, document_type, proc_status, response)

        return response, 200
