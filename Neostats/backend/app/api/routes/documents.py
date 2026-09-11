from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any

from backend.app.services.document_service import DocumentService
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.core.logging import logger

router = APIRouter()

@router.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint for deployed service (Section 5 & 7 requirement).
    """
    return {
        "status": "healthy",
        "service": "NeoStats Document Intelligence Platform",
        "version": "1.0.0"
    }

@router.post("/documents/process", tags=["Documents"])
async def process_document(
    file: UploadFile = File(...),
    document_type: str = Form(...)
):
    """
    Upload and process a PDF / JPG / PNG financial document (Section 5.1).
    Supported document_type values: invoice | balance_sheet | profit_and_loss | cash_flow_statement
    """
    try:
        content = await file.read()
        res_dict, status_code = DocumentService.process_document(
            file_name=file.filename,
            content=content,
            document_type=document_type,
            content_type=file.content_type
        )
        return JSONResponse(content=res_dict, status_code=status_code)
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred while processing the document."
                }
            }
        )

@router.get("/documents/{document_name}", tags=["Documents"])
def get_document_by_name(document_name: str):
    """
    Retrieve the latest structured result using the document/file name (Section 5.1).
    """
    result = DocumentRepository.get_by_name(document_name)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_name}' not found."
        )
    return result

@router.get("/documents", tags=["Documents"])
def list_documents():
    """
    List all processed documents for the frontend dashboard (Section 5.1 & 6).
    """
    return DocumentRepository.list_all()
