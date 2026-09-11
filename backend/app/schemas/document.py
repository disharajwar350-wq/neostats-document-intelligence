from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    INVOICE = "invoice"
    BALANCE_SHEET = "balance_sheet"
    PROFIT_AND_LOSS = "profit_and_loss"
    CASH_FLOW_STATEMENT = "cash_flow_statement"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Evidence(BaseModel):
    source_text: str | None = None
    page_number: int | None = Field(default=None, ge=1)


class ExtractedValue(BaseModel):
    value: Any = None
    evidence: Evidence | None = None


class FileValidation(BaseModel):
    file_type: str
    is_supported: bool
    is_readable: bool
    page_count: int | None = None
    status: ValidationStatus
    error_code: str | None = None
    message: str | None = None


class ValidationCheck(BaseModel):
    name: str
    formula: str
    operands: dict[str, Any]
    calculated_value: float | None = None
    reported_value: float | None = None
    variance: float | None = None
    status: ValidationStatus


class FinancialValidation(BaseModel):
    checks: list[ValidationCheck] = Field(default_factory=list)
    overall_status: ValidationStatus
    issues: list[str] = Field(default_factory=list)


class ProcessingMetadata(BaseModel):
    ocr_used: bool = False
    processed_at: datetime
    processing_time_ms: int


class DocumentResult(BaseModel):
    document_name: str
    document_type: DocumentType
    processing_status: ValidationStatus
    file_validation: FileValidation
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    validation: FinancialValidation
    processing_metadata: ProcessingMetadata

