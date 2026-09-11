from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class FileValidationSchema(BaseModel):
    file_type: str
    is_supported: bool
    is_readable: bool
    page_count: int
    status: str  # "PASS" | "FAILED"

class EvidenceSchema(BaseModel):
    source_text: Optional[str] = None
    page_number: Optional[int] = 1

class ExtractedFieldSchema(BaseModel):
    value: Any = None
    confidence: Optional[float] = None
    page_number: Optional[int] = 1
    evidence: Optional[EvidenceSchema] = None

class LineItemSchema(BaseModel):
    description: str
    quantity: Optional[float] = 1.0
    unit_price: Optional[float] = 0.0
    amount: Optional[float] = 0.0

class ValidationCheckSchema(BaseModel):
    name: str
    formula: str
    operands: Dict[str, Any]
    calculated_value: Optional[float]
    reported_value: Optional[float]
    variance: Optional[float]
    status: str  # "PASS" | "FAIL" | "NOT_APPLICABLE"

class ValidationSectionSchema(BaseModel):
    checks: List[ValidationCheckSchema]
    overall_status: str
    issues: List[str]

class ProcessingMetadataSchema(BaseModel):
    ocr_used: bool = True
    processed_at: str
    processing_time_ms: int

class ProcessDocumentResponse(BaseModel):
    document_name: str
    document_type: str
    processing_status: str  # "PASS" | "FAILED"
    overall_confidence: Optional[float] = None
    file_validation: FileValidationSchema
    extracted_data: Dict[str, Any]
    validation: ValidationSectionSchema
    processing_metadata: ProcessingMetadataSchema

class ErrorResponse(BaseModel):
    error: Dict[str, str]
