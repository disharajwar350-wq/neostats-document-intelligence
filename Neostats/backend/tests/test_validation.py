import pytest
from backend.app.services.financial_validation_service import FinancialValidationService
from backend.app.services.document_validation_service import DocumentValidationService

def test_invoice_financial_validation_pass():
    data = {
        "subtotal": {"value": 1000.0},
        "tax_amount": {"value": 100.0},
        "discount": {"value": 50.0},
        "shipping_and_handling": {"value": 0.0},
        "total_amount": {"value": 1050.0}
    }
    result = FinancialValidationService.validate_document("invoice", data)
    assert result["overall_status"] == "PASS"
    assert len(result["checks"]) == 2
    assert result["checks"][0]["status"] == "PASS"
    assert result["checks"][0]["calculated_value"] == 1050.0

def test_invoice_financial_validation_fail():
    data = {
        "subtotal": {"value": 1000.0},
        "tax_amount": {"value": 100.0},
        "discount": {"value": 50.0},
        "shipping_and_handling": {"value": 0.0},
        "total_amount": {"value": 9999.0} # Incorrect total
    }
    result = FinancialValidationService.validate_document("invoice", data)
    assert result["overall_status"] == "FAIL"
    assert result["checks"][0]["status"] == "FAIL"
    assert result["checks"][0]["variance"] == 8949.0

def test_balance_sheet_validation():
    data = {
        "total_assets": {"value": 50000.0},
        "total_liabilities": {"value": 30000.0},
        "total_equity": {"value": 20000.0}
    }
    result = FinancialValidationService.validate_document("balance_sheet", data)
    assert result["overall_status"] == "PASS"
    assert result["checks"][0]["calculated_value"] == 50000.0

def test_file_validation_unsupported():
    is_valid, res = DocumentValidationService.validate_file("test.exe", b"invalid binary")
    assert is_valid is False
    assert res["is_supported"] is False
    assert res["status"] == "FAILED"
