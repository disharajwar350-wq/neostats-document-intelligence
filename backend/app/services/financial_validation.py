from math import isclose
from typing import Any

from app.schemas.document import FinancialValidation, ValidationCheck, ValidationStatus


def _number(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    if isinstance(value, dict):
        value = value.get("value")
    return float(value) if isinstance(value, (int, float)) else None


def validate_financials(document_type: str, data: dict[str, Any]) -> FinancialValidation:
    if document_type == "invoice":
        subtotal, tax, discount, shipping, total = (_number(data, key) for key in
                                                     ("subtotal", "tax_amount", "discount",
                                                      "shipping_and_handling", "total_amount"))
        if subtotal is None or total is None:
            return FinancialValidation(checks=[], overall_status=ValidationStatus.NOT_APPLICABLE)
        tax = tax or 0.0
        discount = discount or 0.0
        shipping = shipping or 0.0
        calculated = subtotal + tax + shipping - discount
        variance = calculated - total
        status = ValidationStatus.PASS if isclose(calculated, total, abs_tol=0.01) else ValidationStatus.FAIL
        check = ValidationCheck(
            name="invoice_total_check",
            formula="subtotal + tax_amount + shipping_and_handling - discount",
            operands={"subtotal": subtotal, "tax_amount": tax, "shipping_and_handling": shipping,
                      "discount": discount},
            calculated_value=calculated,
            reported_value=total,
            variance=variance,
            status=status,
        )
        checks = [check]
        for index, item in enumerate(data.get("line_items", []), 1):
            quantity, unit_price, amount = (item.get(key) for key in ("quantity", "unit_price", "amount"))
            if quantity is None or unit_price is None or amount is None:
                continue
            calculated_line = quantity * unit_price
            line_status = ValidationStatus.PASS if isclose(calculated_line, amount, abs_tol=0.01) else ValidationStatus.FAIL
            checks.append(ValidationCheck(
                name=f"invoice_line_{index}_check",
                formula="quantity * unit_price",
                operands={"quantity": quantity, "unit_price": unit_price},
                calculated_value=calculated_line,
                reported_value=amount,
                variance=calculated_line - amount,
                status=line_status,
            ))
        overall = ValidationStatus.FAIL if any(c.status == ValidationStatus.FAIL for c in checks) else status
        return FinancialValidation(
            checks=checks,
            overall_status=overall,
            issues=[] if overall == ValidationStatus.PASS else ["One or more invoice values do not reconcile."],
        )

    rules = {
        "balance_sheet": ("balance_sheet_check", "total_assets", "total_liabilities", "total_equity",
                          "total_liabilities + total_equity", "Liabilities and equity do not reconcile to assets."),
        "profit_and_loss": ("profit_check", "revenue", "cost_of_sales", "gross_profit",
                            "revenue - cost_of_sales", "Revenue and cost of sales do not reconcile to gross profit."),
        "cash_flow_statement": ("cash_flow_check", "opening_cash", "net_change_in_cash", "closing_cash",
                                "opening_cash + net_change_in_cash", "Opening cash and net change do not reconcile to closing cash."),
    }
    rule = rules.get(document_type)
    if not rule:
        return FinancialValidation(checks=[], overall_status=ValidationStatus.NOT_APPLICABLE)
    name, first_key, second_key, reported_key, formula, issue = rule
    first, second, reported = (_number(data, key) for key in (first_key, second_key, reported_key))
    if first is None or second is None or reported is None:
        return FinancialValidation(checks=[], overall_status=ValidationStatus.NOT_APPLICABLE)
    if document_type == "balance_sheet":
        calculated, reported_value = second + reported, first
        operands = {second_key: second, reported_key: reported}
    elif document_type == "profit_and_loss":
        calculated, reported_value = first - second, reported
        operands = {first_key: first, second_key: second}
    else:
        calculated, reported_value = first + second, reported
        operands = {first_key: first, second_key: second}
    variance = calculated - reported_value
    status = ValidationStatus.PASS if isclose(calculated, reported_value, abs_tol=0.01) else ValidationStatus.FAIL
    return FinancialValidation(
        checks=[ValidationCheck(name=name, formula=formula,
                                operands=operands,
                                calculated_value=calculated, reported_value=reported_value,
                                variance=variance, status=status)],
        overall_status=status,
        issues=[] if status == ValidationStatus.PASS else [issue],
    )
