from app.services.financial_validation import validate_financials


def test_invoice_total_passes():
    result = validate_financials("invoice", {
        "subtotal": 100,
        "tax_amount": 10,
        "discount": 5,
        "total_amount": 105,
    })
    assert result.overall_status == "PASS"


def test_missing_invoice_fields_are_not_applicable():
    result = validate_financials("invoice", {"subtotal": 100})
    assert result.overall_status == "NOT_APPLICABLE"


def test_balance_sheet_reconciles():
    result = validate_financials("balance_sheet", {
        "total_assets": 1000,
        "total_liabilities": 600,
        "total_equity": 400,
    })
    assert result.overall_status == "PASS"


def test_cash_flow_parentheses_are_supported_by_numeric_input():
    result = validate_financials("cash_flow_statement", {
        "opening_cash": 100,
        "net_change_in_cash": -25,
        "closing_cash": 75,
    })
    assert result.overall_status == "PASS"
