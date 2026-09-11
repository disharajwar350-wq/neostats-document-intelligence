from backend.app.services.extraction_service import ExtractionService
from backend.app.services.financial_validation_service import FinancialValidationService


def _pages(*lines):
    return [{"page_number": 1, "text": "\n".join(lines), "lines": list(lines)}]


def test_cash_flow_supports_fragmented_labels_and_reconciliation():
    extracted = ExtractionService.extract(
        "Cash Flow",
        _pages(
            "Net cash flow from / (used in) operating activities",
            "424,764,563",
            "Net cash flow used in investing activities",
            "(16,808,651)",
            "Net cash flow (used in) / from financing activities",
            "(73,213,515)",
            "Effect of exchange fluctuation on translation reserve",
            "(1,418,252)",
            "Net increase / (decrease) in cash and cash equivalents",
            "333,324,145",
            "Cash and cash equivalents as at April 1st",
            "879,401,119",
            "Cash and cash equivalents as at March 31st",
            "1,212,725,264",
        ),
    )
    validation = FinancialValidationService.validate_document("Cash Flow", extracted)
    assert extracted["operating_cash_flow"]["value"] == 424764563.0
    assert extracted["closing_cash"]["value"] == 1212725264.0
    assert all(check["status"] != "FAIL" for check in validation["checks"])


def test_invoice_supports_sales_tax_shipping_and_standalone_total():
    extracted = ExtractionService.extract(
        "Invoice",
        _pages(
            "Invoice#: 6825",
            "Subtotal $135.00",
            "Sales Tax 8% $12.48",
            "Shipping and Handling $10.00",
            "Total Due",
            "$157.48",
        ),
    )
    validation = FinancialValidationService.validate_document("Invoice", extracted)
    assert extracted["tax_amount"]["value"] == 12.48
    assert extracted["shipping_and_handling"]["value"] == 10.0
    assert extracted["total_amount"]["value"] == 157.48
    assert validation["overall_status"] == "PASS"


def test_invoice_tolerance_is_explicit():
    result = FinancialValidationService.validate_document(
        "Invoice",
        {
            "subtotal": {"value": 804.0},
            "tax_amount": {"value": 63.47},
            "shipping_and_handling": {"value": 50.0},
            "discount": {"value": 0.0},
            "total_amount": {"value": 916.47},
        },
    )
    assert result["overall_status"] == "PASS"
    assert result["checks"][0]["status"] == "PASS_WITH_TOLERANCE"
    assert result["checks"][0]["variance"] == 1.0
