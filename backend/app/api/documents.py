from datetime import datetime, timezone
from time import perf_counter

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.document import (
    DocumentResult, DocumentType,     FileValidation,
    FinancialValidation, ProcessingMetadata, ValidationStatus,
)
from app.services.extractor import extract_text
from app.services.file_validator import validate_file
from app.services.financial_validation import validate_financials
from app.services.persistence import get, list_documents, save
from app.services.schema_extractor import extract_structured


router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/process", response_model=DocumentResult, status_code=201)
async def process_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
) -> DocumentResult:
    started = perf_counter()
    content = await file.read()
    validated = validate_file(file.filename or "", content)
    file_validation = FileValidation(
        file_type=validated.mime_type,
        is_supported=validated.extension in {".pdf", ".jpg", ".jpeg", ".png"},
        is_readable=validated.is_readable,
        page_count=validated.page_count or None,
        status=ValidationStatus.PASS if validated.is_readable else ValidationStatus.FAIL,
        error_code=validated.error_code,
        message=validated.message,
    )
    if not validated.is_readable:
        raise HTTPException(status_code=400, detail={"code": validated.error_code, "message": validated.message})

    extraction = extract_text(content, validated.extension)
    extracted = extract_structured(extraction.text, extraction.pages, document_type.value)
    financial = validate_financials(document_type.value, extracted)
    processing_status = ValidationStatus.PASS if extraction.text.strip() else ValidationStatus.FAIL
    if processing_status == ValidationStatus.FAIL:
        financial.issues.append("No readable text was extracted from the document.")
    processed_at = datetime.now(timezone.utc)
    result = DocumentResult(
        document_name=file.filename or "unnamed",
        document_type=document_type,
        processing_status=processing_status,
        file_validation=file_validation,
        extracted_data=extracted,
        validation=financial,
        processing_metadata=ProcessingMetadata(
            ocr_used=extraction.ocr_used,
            processed_at=processed_at,
            processing_time_ms=round((perf_counter() - started) * 1000),
        ),
    )
    save(result.model_dump(mode="json"))
    return result


@router.get("", response_model=list[DocumentResult])
def documents() -> list[dict]:
    return list_documents()


@router.get("/{document_name}", response_model=DocumentResult)
def document_by_name(document_name: str) -> dict:
    result = get(document_name)
    if not result:
        raise HTTPException(status_code=404, detail="Document result not found.")
    return result
