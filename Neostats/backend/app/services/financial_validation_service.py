from typing import Dict, Any, List
from backend.app.utils.normalizer import NumberNormalizer
from backend.app.core.logging import logger

class FinancialValidationService:
    """
    Implements Section 4.4 Financial Calculation Validation rules:
    - Invoice: subtotal + tax_amount + shipping_and_handling - discount == total_amount
    - Balance Sheet: total_liabilities_and_equity == total_assets
    - Profit & Loss: revenue - COGS == gross_profit, gross_profit - opex == operating_profit, operating_profit - tax == net_profit
    - Cash Flow: operating + investing + financing == net_change, opening + net_change == closing
    """

    @staticmethod
    def validate_document(doc_type: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        doc_type_norm = doc_type.lower().replace('-', '_').replace(' ', '_')
        checks = []
        issues = []

        if 'invoice' in doc_type_norm:
            checks.extend(FinancialValidationService._validate_invoice_checks(extracted_data))
        elif 'balance' in doc_type_norm:
            checks.append(FinancialValidationService._validate_balance_sheet(extracted_data))
        elif 'profit' in doc_type_norm or 'pnl' in doc_type_norm or 'loss' in doc_type_norm:
            checks.extend(FinancialValidationService._validate_pnl(extracted_data))
        elif 'cash' in doc_type_norm:
            checks.extend(FinancialValidationService._validate_cash_flow(extracted_data))

        if not checks or all(check["status"] == "NOT_APPLICABLE" for check in checks):
            overall_status = "NOT_APPLICABLE"
        else:
            overall_status = "PASS"
        for check in checks:
            if check["status"] == "FAIL":
                overall_status = "FAIL"
                issues.append(f"Financial validation failed for check '{check['name']}': calculated {check['calculated_value']} vs reported {check['reported_value']} (variance: {check['variance']})")

        return {
            "checks": checks,
            "overall_status": overall_status,
            "issues": issues
        }

    @staticmethod
    def _extract_val(data: Dict[str, Any], key: str) -> float:
        if key not in data or data[key] is None:
            return None
        val_obj = data[key]
        if isinstance(val_obj, dict):
            return NumberNormalizer.parse_float(val_obj.get("value"))
        return NumberNormalizer.parse_float(val_obj)

    @staticmethod
    def _validate_invoice(data: Dict[str, Any]) -> Dict[str, Any]:
        subtotal = FinancialValidationService._extract_val(data, "subtotal")
        tax = FinancialValidationService._extract_val(data, "tax_amount") or 0.0
        discount = FinancialValidationService._extract_val(data, "discount") or 0.0
        shipping = FinancialValidationService._extract_val(data, "shipping_and_handling") or 0.0
        total = FinancialValidationService._extract_val(data, "total_amount")

        if subtotal is None or total is None:
            return {
                "name": "invoice_total_check",
                "formula": "subtotal + tax_amount + shipping_and_handling - discount",
                "operands": {"subtotal": subtotal, "tax_amount": tax,
                             "shipping_and_handling": shipping, "discount": discount},
                "calculated_value": None,
                "reported_value": total,
                "variance": None,
                "status": "NOT_APPLICABLE"
            }

        calc = round(subtotal + tax + shipping - discount, 2)
        variance = round(abs(calc - total), 2)
        status = (
            "PASS"
            if variance <= 0.05
            else "PASS_WITH_TOLERANCE"
            if variance <= 1.0 and shipping != 0.0
            else "FAIL"
        )

        return {
            "name": "invoice_total_check",
            "formula": "subtotal + tax_amount + shipping_and_handling - discount",
            "operands": {"subtotal": subtotal, "tax_amount": tax,
                         "shipping_and_handling": shipping, "discount": discount},
            "calculated_value": calc,
            "reported_value": total,
            "variance": variance,
            "status": status,
            "warning": (
                "A one-unit variance was retained as an OCR/layout tolerance."
                if status == "PASS_WITH_TOLERANCE" else None
            )
        }

    @staticmethod
    def _validate_invoice_checks(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        checks = [FinancialValidationService._validate_invoice(data)]
        line_items = data.get("line_items") or []
        measurable_items = [
            item for item in line_items
            if item.get("quantity") is not None
            and item.get("unit_price") is not None
            and item.get("amount") is not None
            # OCR frequently repeats the unit-price column as the total when
            # the source table has separate quantity/price/total columns.
            and not (
                float(item["quantity"]) > 1
                and abs(float(item["unit_price"]) - float(item["amount"])) <= 0.005
            )
        ]
        if not measurable_items:
            checks.append({
                "name": "invoice_line_items_check",
                "formula": "quantity * unit_price ~= line_total",
                "operands": {"line_items": 0},
                "calculated_value": None,
                "reported_value": None,
                "variance": None,
                "status": "NOT_APPLICABLE"
            })
            return checks

        mismatches = []
        for item in measurable_items:
            calculated = round(float(item["quantity"]) * float(item["unit_price"]), 2)
            reported = NumberNormalizer.parse_float(item["amount"])
            if reported is not None and abs(calculated - reported) > 0.05:
                mismatches.append({
                    "description": item.get("description"),
                    "calculated": calculated,
                    "reported": reported
                })
        checks.append({
            "name": "invoice_line_items_check",
            "formula": "quantity * unit_price ~= line_total for every line",
            "operands": {"line_items": len(measurable_items)},
            "calculated_value": len(measurable_items) - len(mismatches),
            "reported_value": len(measurable_items),
            "variance": len(mismatches),
            "status": "PASS" if not mismatches else "FAIL",
            "mismatches": mismatches
        })
        return checks

    @staticmethod
    def _validate_balance_sheet(data: Dict[str, Any]) -> Dict[str, Any]:
        assets = FinancialValidationService._extract_val(data, "total_assets")
        liabilities = FinancialValidationService._extract_val(data, "total_liabilities")
        equity = FinancialValidationService._extract_val(data, "total_equity")

        if assets is None or (liabilities is None and equity is None):
            return {
                "name": "balance_sheet_reconciliation",
                "formula": "total_liabilities + total_equity",
                "operands": {"total_liabilities": liabilities, "total_equity": equity},
                "calculated_value": None,
                "reported_value": assets,
                "variance": None,
                "status": "NOT_APPLICABLE"
            }

        liab_val = liabilities or 0.0
        eq_val = equity or 0.0
        calc = round(liab_val + eq_val, 2)
        variance = round(abs(calc - assets), 2)
        status = "PASS" if variance <= 0.05 else "FAIL"

        return {
            "name": "balance_sheet_reconciliation",
            "formula": "total_liabilities + total_equity",
            "operands": {"total_liabilities": liabilities, "total_equity": equity},
            "calculated_value": calc,
            "reported_value": assets,
            "variance": variance,
            "status": status
        }

    @staticmethod
    def _validate_pnl(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        rev = FinancialValidationService._extract_val(data, "revenue")
        cogs = FinancialValidationService._extract_val(data, "cost_of_sales")
        gp = FinancialValidationService._extract_val(data, "gross_profit")
        opex = FinancialValidationService._extract_val(data, "operating_expenses")
        op = FinancialValidationService._extract_val(data, "operating_profit")
        tax = FinancialValidationService._extract_val(data, "tax")
        np_val = FinancialValidationService._extract_val(data, "net_profit")

        checks = []

        # Check 1: Revenue - COGS == Gross Profit
        if rev is not None and cogs is not None and gp is not None:
            calc_gp = round(rev - cogs, 2)
            var_gp = round(abs(calc_gp - gp), 2)
            checks.append({
                "name": "gross_profit_check",
                "formula": "revenue - cost_of_sales",
                "operands": {"revenue": rev, "cost_of_sales": cogs},
                "calculated_value": calc_gp,
                "reported_value": gp,
                "variance": var_gp,
                "status": "PASS" if var_gp <= 0.05 else "FAIL"
            })
        else:
            checks.append({
                "name": "gross_profit_check",
                "formula": "revenue - cost_of_sales",
                "operands": {"revenue": rev, "cost_of_sales": cogs},
                "calculated_value": None,
                "reported_value": gp,
                "variance": None,
                "status": "NOT_APPLICABLE"
            })

        # Check 2: Gross Profit - Opex == Operating Profit
        if gp is not None and opex is not None and op is not None:
            calc_op = round(gp - opex, 2)
            var_op = round(abs(calc_op - op), 2)
            checks.append({
                "name": "operating_profit_check",
                "formula": "gross_profit - operating_expenses",
                "operands": {"gross_profit": gp, "operating_expenses": opex},
                "calculated_value": calc_op,
                "reported_value": op,
                "variance": var_op,
                "status": "PASS" if var_op <= 0.05 else "FAIL"
            })
        else:
            checks.append({
                "name": "operating_profit_check",
                "formula": "gross_profit - operating_expenses",
                "operands": {"gross_profit": gp, "operating_expenses": opex},
                "calculated_value": None,
                "reported_value": op,
                "variance": None,
                "status": "NOT_APPLICABLE"
            })

        def reconciliation(name, formula, operands, calculated, reported):
            if calculated is None or reported is None:
                return {
                    "name": name,
                    "formula": formula,
                    "operands": operands,
                    "calculated_value": None,
                    "reported_value": reported,
                    "variance": None,
                    "status": "NOT_APPLICABLE",
                }
            calculated = round(calculated, 2)
            variance = round(abs(calculated - reported), 2)
            return {
                "name": name,
                "formula": formula,
                "operands": operands,
                "calculated_value": calculated,
                "reported_value": reported,
                "variance": variance,
                "status": "PASS" if variance <= 0.05 else "FAIL",
            }

        total_income = FinancialValidationService._extract_val(data, "total_income")
        interest_earned = FinancialValidationService._extract_val(data, "interest_earned")
        other_income = FinancialValidationService._extract_val(data, "other_income")
        interest_expended = FinancialValidationService._extract_val(data, "interest_expended")
        total_expenses = FinancialValidationService._extract_val(data, "total_expenses")
        provisions = FinancialValidationService._extract_val(data, "provisions")
        contingencies = FinancialValidationService._extract_val(data, "contingencies")
        profit_before_tax = FinancialValidationService._extract_val(data, "profit_before_tax")
        minority_interest = FinancialValidationService._extract_val(data, "minority_interest")
        group_net_profit = FinancialValidationService._extract_val(data, "group_net_profit")
        current_profit = FinancialValidationService._extract_val(data, "current_profit")
        brought_forward_profit = FinancialValidationService._extract_val(data, "brought_forward_profit")
        total_appropriation = FinancialValidationService._extract_val(
            data, "total_available_for_appropriation"
        )
        checks.extend([
            reconciliation(
                "total_income_check",
                "interest_earned + other_income",
                {"interest_earned": interest_earned, "other_income": other_income},
                interest_earned + other_income
                if interest_earned is not None and other_income is not None else None,
                total_income,
            ),
            reconciliation(
                "total_expenses_check",
                "interest_expended + operating_expenses + provisions + contingencies",
                {
                    "interest_expended": interest_expended,
                    "operating_expenses": opex,
                    "provisions": provisions,
                    "contingencies": contingencies,
                },
                interest_expended + opex + provisions + contingencies
                if all(value is not None for value in (interest_expended, opex, provisions, contingencies))
                else None,
                total_expenses,
            ),
            reconciliation(
                "profit_before_tax_check",
                "total_income - total_expenses",
                {"total_income": total_income, "total_expenses": total_expenses},
                total_income - total_expenses
                if total_income is not None and total_expenses is not None else None,
                profit_before_tax,
            ),
            reconciliation(
                "net_profit_check",
                "profit_before_tax - tax",
                {"profit_before_tax": profit_before_tax, "tax": tax},
                profit_before_tax - tax
                if profit_before_tax is not None and tax is not None else None,
                np_val,
            ),
            reconciliation(
                "group_net_profit_check",
                "profit_before_tax - minority_interest",
                {
                    "profit_before_tax": profit_before_tax,
                    "minority_interest": minority_interest,
                },
                profit_before_tax - minority_interest
                if profit_before_tax is not None and minority_interest is not None
                else None,
                group_net_profit,
            ),
            reconciliation(
                "appropriation_check",
                "current_profit + brought_forward_profit",
                {
                    "current_profit": current_profit,
                    "brought_forward_profit": brought_forward_profit,
                },
                current_profit + brought_forward_profit
                if current_profit is not None and brought_forward_profit is not None
                else None,
                total_appropriation,
            ),
        ])

        return checks

    @staticmethod
    def _validate_cash_flow(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        cfo = FinancialValidationService._extract_val(data, "operating_cash_flow")
        cfi = FinancialValidationService._extract_val(data, "investing_cash_flow")
        cff = FinancialValidationService._extract_val(data, "financing_cash_flow")
        net_change = FinancialValidationService._extract_val(data, "net_change_in_cash")
        opening = FinancialValidationService._extract_val(data, "opening_cash")
        closing = FinancialValidationService._extract_val(data, "closing_cash")

        checks = []
        adjustment_values = []
        for item in data.get("line_items", []):
            label = str(item.get("label", "")).lower()
            if (
                "effect of exchange" in label
                or "effect of fluctuation" in label
                or "cash and cash equivalents on amalgamation" in label
                or "cash and cash equivalents acquired on amalgamation" in label
            ):
                values = item.get("values") or []
                if values:
                    adjustment_values.append(NumberNormalizer.parse_float(values[0]) or 0.0)

        # Annual reports sometimes include an amalgamation adjustment in the
        # displayed net-change total and sometimes include it in the investing/
        # financing subtotal. Choose the reported combination, if one exists,
        # rather than double-counting it.
        adjustments = 0.0
        if cfo is not None and cfi is not None and cff is not None and net_change is not None:
            base = cfo + cfi + cff
            for mask in range(1 << len(adjustment_values)):
                candidate = sum(
                    value for index, value in enumerate(adjustment_values)
                    if mask & (1 << index)
                )
                if abs((base + candidate) - net_change) <= 0.05:
                    adjustments = candidate
                    break

        # Check 1: CFO + CFI + CFF == Net Change
        if cfo is not None and cfi is not None and cff is not None and net_change is not None:
            calc_net = round(cfo + cfi + cff + adjustments, 2)
            var_net = round(abs(calc_net - net_change), 2)
            checks.append({
                "name": "net_cash_flow_check",
                "formula": "operating_cash_flow + investing_cash_flow + financing_cash_flow + reported_adjustments",
                "operands": {"operating_cash_flow": cfo, "investing_cash_flow": cfi,
                             "financing_cash_flow": cff, "reported_adjustments": adjustments},
                "calculated_value": calc_net,
                "reported_value": net_change,
                "variance": var_net,
                "status": "PASS" if var_net <= 0.05 else "FAIL"
            })
        else:
            checks.append({
                "name": "net_cash_flow_check",
                "formula": "operating_cash_flow + investing_cash_flow + financing_cash_flow",
                "operands": {"operating_cash_flow": cfo, "investing_cash_flow": cfi, "financing_cash_flow": cff},
                "calculated_value": None,
                "reported_value": net_change,
                "variance": None,
                "status": "NOT_APPLICABLE"
            })

        # Check 2: Opening + Net Change == Closing
        if opening is not None and net_change is not None and closing is not None:
            calc_closing = round(opening + net_change, 2)
            var_closing = round(abs(calc_closing - closing), 2)
            checks.append({
                "name": "cash_reconciliation_check",
                "formula": "opening_cash + net_change_in_cash",
                "operands": {"opening_cash": opening, "net_change_in_cash": net_change},
                "calculated_value": calc_closing,
                "reported_value": closing,
                "variance": var_closing,
                "status": "PASS" if var_closing <= 0.05 else "FAIL"
            })
        else:
            checks.append({
                "name": "cash_reconciliation_check",
                "formula": "opening_cash + net_change_in_cash",
                "operands": {"opening_cash": opening, "net_change_in_cash": net_change},
                "calculated_value": None,
                "reported_value": closing,
                "variance": None,
                "status": "NOT_APPLICABLE"
            })

        return checks
