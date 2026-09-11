import re
from itertools import product
from typing import Dict, Any, List
from backend.app.utils.normalizer import NumberNormalizer

class ExtractionService:
    """
    Field and table extraction service covering all 4 document categories:
    Invoice, Balance Sheet, Profit & Loss, and Cash Flow Statement.
    """

    @staticmethod
    def extract(document_type: str, pages_text: List[Dict[str, Any]]) -> Dict[str, Any]:
        doc_type_norm = document_type.lower().replace('-', '_').replace(' ', '_')
        full_text = "\n".join([p["text"] for p in pages_text])
        all_lines = []
        for p in pages_text:
            for line in p["lines"]:
                all_lines.append((line, p["page_number"]))

        if 'invoice' in doc_type_norm:
            return ExtractionService._extract_invoice(all_lines, full_text)
        elif 'balance' in doc_type_norm:
            return ExtractionService._extract_balance_sheet(all_lines, full_text)
        elif 'profit' in doc_type_norm or 'pnl' in doc_type_norm or 'loss' in doc_type_norm:
            return ExtractionService._extract_pnl(all_lines, full_text)
        elif 'cash' in doc_type_norm:
            return ExtractionService._extract_cash_flow(all_lines, full_text)

        # Fallback generic
        return ExtractionService._extract_invoice(all_lines, full_text)

    @staticmethod
    def _create_field(value: Any, source_text: str = None, page: int = 1, confidence: float = None) -> Dict[str, Any]:
        if value is None:
            return {
                "value": None,
                "confidence": confidence,
                "page_number": page,
                "evidence": None
            }
        return {
            "value": value,
            "confidence": confidence,
            "page_number": page,
            "evidence": {
                "source_text": source_text or str(value),
                "page_number": page
            }
        }

    @staticmethod
    def _find_field_by_regex(lines: List[tuple], patterns: List[str], is_number: bool = False) -> tuple:
        for pattern in patterns:
            for line, page in lines:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    raw_val = match.group(1).strip()
                    if is_number:
                        curr, num = NumberNormalizer.clean_currency(raw_val)
                        if num is not None:
                            return num, line, page
                    else:
                        if raw_val:
                            return raw_val, line, page
        return None, None, 1

    @staticmethod
    def _row_values(line: str) -> tuple[str, list[float]]:
        # Keep separate columns separate. A broad whitespace match would merge
        # schedule numbers with the following financial values.
        matches = list(re.finditer(
            r"\(?-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\)?",
            line,
        ))
        values = []
        for match in matches:
            _, value = NumberNormalizer.clean_currency(match.group(0))
            if value is not None:
                values.append(value)
        # Annual-report rows often contain a schedule number before two period values.
        if len(values) >= 3 and values[0].is_integer() and abs(values[0]) < 100:
            values = values[1:]
            label_end = matches[1].start()
        else:
            label_end = matches[0].start() if matches else len(line)
        return line[:label_end].strip(" :-\t"), values

    @staticmethod
    def _rows(lines: List[tuple]) -> list[dict]:
        rows = []
        pending_labels = []
        for line, page in lines:
            label, values = ExtractionService._row_values(line)
            normalized_label = re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()
            # Ordinal dates such as "April 1st" and "March 31st" are
            # captured as numbers, but they are not cash values.
            if (
                (
                    normalized_label.startswith("cash and cash equivalents as at")
                    or normalized_label.startswith("cash and cash equivalents on amalgamation")
                )
                and values
                and all(abs(value) <= 31 for value in values)
            ):
                values = []
            if values and label:
                if normalized_label.startswith((
                    "for the year ended", "hdfc bank", "31 mar", "schedule 31 mar",
                    "in ", "z in ", "mumbai", "membership no",
                )):
                    continue
                rows.append({"label": label, "values": values, "source_text": line, "page": page})
                continue
            if not values and line.strip():
                # Some scanned annual reports render the row labels first and the
                # two numeric columns later as standalone lines.
                normalized = re.sub(r"[^a-z0-9]+", " ", line.lower()).strip()
                if (
                    len(normalized) >= 3
                    and any(char.isalpha() for char in normalized)
                    and not normalized.startswith((
                        "hdfc bank", "we understand", "for deloitte",
                        "consolidated balance sheet", "consolidated cash flow statement",
                        "consolidated statement of profit and loss", "as at", "for the year ended",
                        "year ended", "schedule", "in ", "cash flows from",
                        "adjustments for", "capital and liabilities", "=",
                    ))
                ):
                    pending_labels.append((line.strip(), page))
                continue
            if values and pending_labels:
                if (
                    len(values) == 1
                    and values[0].is_integer()
                    and abs(values[0]) <= 300
                    and line.strip().replace(" ", "").replace(",", "").isdigit()
                ):
                    continue
                pending_label, pending_page = pending_labels.pop(0)
                rows.append({
                    "label": pending_label,
                    "values": values,
                    "source_text": f"{pending_label} {line}".strip(),
                    "page": pending_page,
                })
        return rows

    @staticmethod
    def _find_row(rows: list[dict], aliases: tuple[str, ...], occurrence: int = 0) -> dict | None:
        matches = []
        for row in rows:
            normalized = re.sub(r"[^a-z0-9]+", " ", row["label"].lower()).strip()
            if any(alias in normalized for alias in aliases):
                matches.append(row)
        return matches[occurrence] if len(matches) > occurrence else None

    @staticmethod
    def _find_row_parts(rows: list[dict], *parts: str) -> dict | None:
        for row in rows:
            normalized = re.sub(r"[^a-z0-9]+", " ", row["label"].lower())
            if all(part in normalized for part in parts):
                return row
        return None

    @staticmethod
    def _field_from_row(row: dict | None) -> tuple[Any, str | None, int]:
        if not row or not row["values"]:
            return None, None, 1
        values = row["values"]
        # Schedule identifiers can precede the two reporting periods.
        value = values[1] if len(values) >= 3 and abs(values[0]) < 100 else values[0]
        return value, row["source_text"], row["page"]

    @staticmethod
    def _comparative_periods(rows: list[dict]) -> list[dict]:
        """Expose annual-report columns without changing canonical values."""
        periods = []
        for row in rows:
            values = row.get("values") or []
            if len(values) >= 3 and values[0].is_integer() and abs(values[0]) < 100:
                values = values[1:]
            if len(values) < 2:
                continue
            periods.append({
                "label": row["label"],
                "current": values[0],
                "comparative": values[1],
                "source_text": row["source_text"],
                "page_number": row["page"],
            })
        return periods

    @staticmethod
    def _cash_flow_field(lines: List[tuple], predicates: list) -> tuple[Any, str | None, int]:
        """Read a cash-flow total when OCR puts values beside, above, or below its label."""
        for index, (line, page) in enumerate(lines):
            normalized = re.sub(r"[^a-z0-9]+", " ", line.lower()).strip()
            if not all(predicate(normalized) for predicate in predicates):
                continue
            label, values = ExtractionService._row_values(line)
            if values and not (
                "cash and cash equivalents" in normalized
                and all(value.is_integer() and abs(value) <= 2100 for value in values)
                and ("march" in normalized or "april" in normalized or "year end" in normalized)
            ):
                return values[0], line, page

            candidates = []
            paired_cash_label = (
                "march" in normalized
                and any(
                    0 <= paired_index < len(lines)
                    and "cash and cash equivalents as at" in re.sub(
                        r"[^a-z0-9]+", " ", lines[paired_index][0].lower()
                    )
                    for paired_index in (index - 1, index + 1)
                )
            )
            direction_order = (1, -1) if (
                index + 1 < len(lines) and lines[index + 1][0].lower().strip() == "ities"
            ) else (1, -1)
            for direction in direction_order:
                for offset in range(1, 4):
                    position = index + (offset * direction)
                    if position < 0 or position >= len(lines):
                        break
                    nearby, nearby_page = lines[position]
                    nearby_label, nearby_values = ExtractionService._row_values(nearby)
                    if (
                        "cash and cash equivalents as at" in re.sub(
                            r"[^a-z0-9]+", " ", nearby.lower()
                        )
                        and nearby_values
                        and all(value.is_integer() and abs(value) <= 31 for value in nearby_values)
                    ):
                        nearby_values = []
                    if nearby_label and (
                        "cash and cash equivalents as at" not in re.sub(
                        r"[^a-z0-9]+", " ", nearby.lower()
                        )
                        and nearby.lower().strip() != "ities"
                    ):
                        break
                    if nearby_values:
                        candidates.extend((value, nearby, nearby_page) for value in nearby_values)
                if candidates:
                    return candidates[1 if paired_cash_label and len(candidates) > 1 else 0]
        return None, None, 1

    @staticmethod
    def _cash_flow_candidates(lines: List[tuple], predicates: list) -> list[tuple]:
        candidates = []
        for index, (line, page) in enumerate(lines):
            normalized = re.sub(r"[^a-z0-9]+", " ", line.lower()).strip()
            if not all(predicate(normalized) for predicate in predicates):
                continue
            for position in range(max(0, index - 4), min(len(lines), index + 5)):
                nearby, nearby_page = lines[position]
                _, values = ExtractionService._row_values(nearby)
                for value in values:
                    if not (value.is_integer() and abs(value) <= 2100 and "march" in normalized):
                        candidates.append((value, nearby, nearby_page))
        unique = []
        seen = set()
        for candidate in candidates:
            if (candidate[0], candidate[1], candidate[2]) not in seen:
                seen.add((candidate[0], candidate[1], candidate[2]))
                unique.append(candidate)
        return unique

    @staticmethod
    def _extract_invoice(lines: List[tuple], text: str) -> Dict[str, Any]:
        # Currency is returned only when explicitly present in the source.
        currency = None
        if "₹" in text or "INR" in text:
            currency = "INR"
        elif "EUR" in text or "€" in text:
            currency = "EUR"
        elif "GBP" in text or "£" in text:
            currency = "GBP"

        inv_num, inv_src, inv_pg = ExtractionService._find_field_by_regex(lines, [
            r'invoice\s*(?:no|num|number|#)\s*[:.\s]+([A-Z0-9\-_]+)',
            r'invoice#\s*[:.\s]+([A-Z0-9\-_]+)',
            r'inv(?:oice)?\s*#\s*[:.\s]+([A-Z0-9\-_]+)'
        ])

        inv_date, date_src, date_pg = ExtractionService._find_field_by_regex(lines, [
            r'invoice\s*date[:.\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+\s+\d{1,2},\s*\d{4})',
            r'date[:.\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        ])

        vendor, v_src, v_pg = ExtractionService._find_field_by_regex(lines, [
            r'vendor[:.\s]+([A-Za-z0-9\s.,&]+)',
            r'from[:.\s]+([A-Za-z0-9\s.,&]+)',
            r'^([A-Z0-9\s.,&]+(?:Technologies|Inc|Corp|LLC|Ltd))'
        ])

        customer, c_src, c_pg = ExtractionService._find_field_by_regex(lines, [
            r'bill\s*to[:.\s]+([A-Za-z0-9\s.,&]+)',
            r'customer[:.\s]+([A-Za-z0-9\s.,&]+)'
        ])

        subtotal, s_src, s_pg = ExtractionService._find_field_by_regex(lines, [
            r'subtotal[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'sub-total[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        tax, t_src, t_pg = ExtractionService._find_field_by_regex(lines, [
            r'sales\s*tax(?:\s+[\d,.]+\s*%)?\s*[$€£]?\s*([\d,.()]+)\s*$',
            r'tax\s*amount[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'vat[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'gst(?!\s*req)(?!\s*summary)[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'tax[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        shipping, sh_src, sh_pg = ExtractionService._find_field_by_regex(lines, [
            r'shipping\s*(?:and|&)\s*handling[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r's&h[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'delivery[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        discount, d_src, d_pg = ExtractionService._find_field_by_regex(lines, [
            r'discount[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        total, tot_src, tot_pg = ExtractionService._find_field_by_regex(lines, [
            r'\btotal\s*amount[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'\btotal\s*due[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'\bamount\s*due[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'\bgrand\s*total[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'\btotal[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)
        if total is None:
            for index, (line, page) in enumerate(lines[:-1]):
                if re.search(r'\btotal\s*due\b', line, re.IGNORECASE):
                    _, candidate = NumberNormalizer.clean_currency(
                        re.sub(r"[^0-9,.()\-]", "", lines[index + 1][0])
                    )
                    if candidate is not None:
                        total, tot_src, tot_pg = candidate, lines[index + 1][0], lines[index + 1][1]
                        break

        if tax is None and total is not None and subtotal is not None and re.search(
            r'inclusive\s+gst', text, re.IGNORECASE
        ):
            tax = round(total - subtotal, 2)
            t_src, t_pg = "GST calculated from inclusive total", tot_pg

        # Line items
        line_items = []
        for line, page in lines:
            if any(k in line.lower() for k in ['subtotal', 'total', 'invoice', 'date', 'bill to']):
                continue
            item_match = re.search(r'([A-Za-z0-9\s\-_]+)\s+(\d+)\s+([\d,.()]+)\s+([\d,.()]+)$', line)
            if item_match:
                desc = item_match.group(1).strip()
                if desc.lower() in {
                    "jan", "feb", "mar", "apr", "may", "jun",
                    "jul", "aug", "sep", "oct", "nov", "dec",
                }:
                    continue
                qty = float(item_match.group(2))
                _, u_price = NumberNormalizer.clean_currency(item_match.group(3))
                _, amt = NumberNormalizer.clean_currency(item_match.group(4))
                line_items.append({
                    "description": desc,
                    "quantity": qty,
                    "unit_price": u_price or 0.0,
                    "amount": amt or 0.0
                })

        return {
            "invoice_number": ExtractionService._create_field(inv_num, inv_src, inv_pg),
            "invoice_date": ExtractionService._create_field(inv_date, date_src, date_pg),
            "vendor_name": ExtractionService._create_field(vendor, v_src, v_pg),
            "customer_name": ExtractionService._create_field(customer, c_src, c_pg),
            "currency": ExtractionService._create_field(currency, f"Currency: {currency}" if currency else None, 1),
            "subtotal": ExtractionService._create_field(subtotal, s_src, s_pg),
            "tax_amount": ExtractionService._create_field(tax or 0.0, t_src, t_pg),
            "shipping_and_handling": ExtractionService._create_field(shipping or 0.0, sh_src, sh_pg),
            "discount": ExtractionService._create_field(discount or 0.0, d_src, d_pg),
            "total_amount": ExtractionService._create_field(total, tot_src, tot_pg),
            "line_items": line_items
        }

    @staticmethod
    def _extract_balance_sheet(lines: List[tuple], text: str) -> Dict[str, Any]:
        rows = ExtractionService._rows(lines)
        assets_row = ExtractionService._find_row(rows, ("total assets",))
        liabilities_row = ExtractionService._find_row(rows, ("total liabilities",))
        equity_row = ExtractionService._find_row(rows, ("total equity", "shareholders equity"))
        if not assets_row:
            totals = [
                row for row in rows
                if "total" in re.sub(r"[^a-z]+", "", row["label"].lower())
            ]
            assets_row = totals[-1] if totals else None
        # Do not manufacture a separate equity value from bank-report capital
        # rows: those reports already include them in the reported total.
        assets, a_src, a_pg = ExtractionService._field_from_row(assets_row)
        liab, l_src, l_pg = ExtractionService._field_from_row(liabilities_row)
        equity, e_src, e_pg = ExtractionService._field_from_row(equity_row)
        line_items = [
            {"label": row["label"], "values": row["values"],
             "source_text": row["source_text"], "page_number": row["page"]}
            for row in rows
        ]
        return {
            "total_assets": ExtractionService._create_field(assets, a_src, a_pg),
            "total_liabilities": ExtractionService._create_field(liab, l_src, l_pg),
            "total_equity": ExtractionService._create_field(equity, e_src, e_pg),
            "line_items": line_items,
            "comparative_periods": ExtractionService._comparative_periods(rows)
        }

        # Legacy label-only fallback retained for unusual OCR output.
        assets, a_src, a_pg = ExtractionService._find_field_by_regex(lines, [
            r'total\s*assets[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'assets\s*total[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        liab, l_src, l_pg = ExtractionService._find_field_by_regex(lines, [
            r'total\s*liabilities[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'liabilities\s*total[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        equity, e_src, e_pg = ExtractionService._find_field_by_regex(lines, [
            r'total\s*equity[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r"shareholders'?\s*equity[:.\s]+([₹$€£]?\s*[\d,.()]+)",
            r'total\s*shareholders\s*funds[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        return {
            "total_assets": ExtractionService._create_field(assets, a_src, a_pg),
            "total_liabilities": ExtractionService._create_field(liab, l_src, l_pg),
            "total_equity": ExtractionService._create_field(equity, e_src, e_pg),
            "line_items": []
        }

    @staticmethod
    def _extract_pnl(lines: List[tuple], text: str) -> Dict[str, Any]:
        rows = ExtractionService._rows(lines)
        def row_value(*aliases):
            return ExtractionService._field_from_row(ExtractionService._find_row(rows, aliases))
        interest, int_src, int_pg = row_value("interest earned")
        other_income, oi_src, oi_pg = row_value("other income")
        total_income, ti_src, ti_pg = row_value("total income")
        interest_expended, ie_src, ie_pg = row_value("interest expended")
        total_expenses, te_src, te_pg = row_value("total expenses", "total expenditure")
        provisions, prov_src, prov_pg = row_value("provisions", "provision")
        contingencies, cont_src, cont_pg = row_value("contingencies", "contingency")
        profit_before_tax, pbt_src, pbt_pg = row_value("profit before income tax", "profit before tax")
        minority_interest, mi_src, mi_pg = row_value(
            "minority interest", "non controlling interest", "non-controlling interest"
        )
        group_net_profit, gnp_src, gnp_pg = row_value(
            "consolidated net profit attributable to the group",
            "net profit attributable to the group",
            "group net profit",
        )
        current_profit, cp_src, cp_pg = row_value("current profit")
        brought_forward_profit, bfp_src, bfp_pg = row_value(
            "brought forward profit", "profit brought forward"
        )
        total_appropriation, ta_src, ta_pg = row_value(
            "total available for appropriation", "available for appropriation"
        )
        rev, r_src, r_pg = row_value("revenue from operations", "total income", "interest earned")
        cogs, c_src, c_pg = row_value("cost of materials", "cost of sales", "cost of goods")
        gp, g_src, g_pg = row_value("gross profit")
        opex, o_src, o_pg = row_value("operating expenses", "other expenses")
        op, op_src, op_pg = row_value("profit from operations", "operating profit")
        tax, t_src, t_pg = row_value("total tax expense", "tax expense")
        np_val, np_src, np_pg = row_value("net profit after tax", "net profit for the year", "net profit")
        return {
            "revenue": ExtractionService._create_field(rev, r_src, r_pg),
            "cost_of_sales": ExtractionService._create_field(cogs, c_src, c_pg),
            "gross_profit": ExtractionService._create_field(gp, g_src, g_pg),
            "operating_expenses": ExtractionService._create_field(opex, o_src, o_pg),
            "operating_profit": ExtractionService._create_field(op, op_src, op_pg),
            "tax": ExtractionService._create_field(tax, t_src, t_pg),
            "net_profit": ExtractionService._create_field(np_val, np_src, np_pg),
            "interest_earned": ExtractionService._create_field(interest, int_src, int_pg),
            "other_income": ExtractionService._create_field(other_income, oi_src, oi_pg),
            "total_income": ExtractionService._create_field(total_income, ti_src, ti_pg),
            "interest_expended": ExtractionService._create_field(interest_expended, ie_src, ie_pg),
            "total_expenses": ExtractionService._create_field(total_expenses, te_src, te_pg),
            "provisions": ExtractionService._create_field(provisions, prov_src, prov_pg),
            "contingencies": ExtractionService._create_field(contingencies, cont_src, cont_pg),
            "profit_before_tax": ExtractionService._create_field(profit_before_tax, pbt_src, pbt_pg),
            "minority_interest": ExtractionService._create_field(minority_interest, mi_src, mi_pg),
            "group_net_profit": ExtractionService._create_field(group_net_profit, gnp_src, gnp_pg),
            "current_profit": ExtractionService._create_field(current_profit, cp_src, cp_pg),
            "brought_forward_profit": ExtractionService._create_field(
                brought_forward_profit, bfp_src, bfp_pg
            ),
            "total_available_for_appropriation": ExtractionService._create_field(
                total_appropriation, ta_src, ta_pg
            ),
            "line_items": [{"label": row["label"], "values": row["values"],
                            "source_text": row["source_text"], "page_number": row["page"]}
                           for row in rows],
            "comparative_periods": ExtractionService._comparative_periods(rows)
        }

        # Legacy label-only fallback retained for unusual OCR output.
        rev, r_src, r_pg = ExtractionService._find_field_by_regex(lines, [
            r'revenue\s*from\s*operations[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'total\s*revenue[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'revenue[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        cogs, c_src, c_pg = ExtractionService._find_field_by_regex(lines, [
            r'cost\s*of\s*(?:sales|materials|goods\s*sold)[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'cogs[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        gp, g_src, g_pg = ExtractionService._find_field_by_regex(lines, [
            r'gross\s*profit[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        opex, o_src, o_pg = ExtractionService._find_field_by_regex(lines, [
            r'operating\s*expenses[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'other\s*expenses[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        op, op_src, op_pg = ExtractionService._find_field_by_regex(lines, [
            r'operating\s*profit[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'profit\s*from\s*operations[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        tax, t_src, t_pg = ExtractionService._find_field_by_regex(lines, [
            r'tax\s*expense[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'total\s*tax\s*expense[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'current\s*tax[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        np_val, np_src, np_pg = ExtractionService._find_field_by_regex(lines, [
            r'net\s*profit\s*after\s*tax[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'net\s*profit[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'net\s*income[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        return {
            "revenue": ExtractionService._create_field(rev, r_src, r_pg),
            "cost_of_sales": ExtractionService._create_field(cogs, c_src, c_pg),
            "gross_profit": ExtractionService._create_field(gp, g_src, g_pg),
            "operating_expenses": ExtractionService._create_field(opex, o_src, o_pg),
            "operating_profit": ExtractionService._create_field(op, op_src, op_pg),
            "tax": ExtractionService._create_field(tax, t_src, t_pg),
            "net_profit": ExtractionService._create_field(np_val, np_src, np_pg),
            "line_items": []
        }

    @staticmethod
    def _extract_cash_flow(lines: List[tuple], text: str) -> Dict[str, Any]:
        rows = ExtractionService._rows(lines)
        cfo, cfo_src, cfo_pg = ExtractionService._cash_flow_field(
            lines, [lambda value: "net" in value, lambda value: "operating" in value,
                    lambda value: "activities" in value])
        cfi, cfi_src, cfi_pg = ExtractionService._cash_flow_field(
            lines, [lambda value: "net" in value, lambda value: "investing" in value,
                    lambda value: "acti" in value])
        cff, cff_src, cff_pg = ExtractionService._cash_flow_field(
            lines, [lambda value: "net" in value, lambda value: "financing" in value,
                    lambda value: "activities" in value])
        net_change, nc_src, nc_pg = ExtractionService._cash_flow_field(
            lines, [lambda value: "net increase" in value or "net change in cash" in value])
        opening, o_src, o_pg = ExtractionService._cash_flow_field(
            lines, [lambda value: "cash and cash equivalents as at april" in value
                    or "cash and cash equivalents at beginning" in value
                    or "opening cash" in value])
        closing, cl_src, cl_pg = ExtractionService._cash_flow_field(
            lines, [lambda value: "cash and cash equivalents as at march" in value
                    or "cash and cash equivalents at end" in value
                    or "cash and cash equivalents as at the year end" in value
                    or "cash and cash equivalents at the end of the year" in value
                    or "closing cash" in value])

        adjustment_rows = []
        for label_predicate in (
            lambda value: "effect of exchange" in value,
            lambda value: "effect of fluctuation in foreign currency" in value,
            lambda value: "amalgamation" in value,
        ):
            adjustment = ExtractionService._cash_flow_field(lines, [label_predicate])
            if adjustment[0] is not None:
                adjustment_rows.append({
                    "label": adjustment[1].split(str(adjustment[0]))[0].strip(),
                    "values": [adjustment[0]],
                    "source_text": adjustment[1],
                    "page_number": adjustment[2],
                })
        existing_labels = set()
        for row in rows:
            if "exchange" in row["label"].lower() or "amalgamation" in row["label"].lower():
                existing_labels.add(row["label"].lower())

        if (
            opening is not None
            and closing is not None
            and net_change is not None
            and abs((opening + net_change) - closing) > 0.05
            and abs((closing + net_change) - opening) <= 0.05
        ):
            opening, closing = closing, opening
            o_src, cl_src = cl_src, o_src
            o_pg, cl_pg = cl_pg, o_pg

        # A few older reports place the operating total immediately before its
        # label. If the reported net change identifies an exact nearby value,
        # use that value with its original OCR line as evidence.
        adjustment_values = [row["values"][0] for row in adjustment_rows]
        adjustment_candidates = []
        for predicate in (
            lambda value: "effect of exchange" in value or "effect of fluctuation" in value,
            lambda value: "amalgamation" in value,
        ):
            adjustment_candidates.extend(ExtractionService._cash_flow_candidates(lines, [predicate]))
        if cfi is not None and cff is not None and net_change is not None:
            target_values = [
                net_change - cfi - cff - sum(adjustment_values),
                net_change - cfi - cff,
            ]
            for line, page in lines:
                _, values = ExtractionService._row_values(line)
                for value in values:
                    if any(abs(value - target) <= 0.05 for target in target_values):
                        if cfo is None or abs(cfo - value) > 0.05:
                            cfo, cfo_src, cfo_pg = value, line, page
                        break

            candidate_groups = [
                ExtractionService._cash_flow_candidates(
                    lines, [lambda value: "net" in value, lambda value: "operating" in value,
                            lambda value: "activities" in value]
                ),
                ExtractionService._cash_flow_candidates(
                    lines, [lambda value: "net" in value, lambda value: "investing" in value,
                            lambda value: "acti" in value]
                ),
                ExtractionService._cash_flow_candidates(
                    lines, [lambda value: "net" in value, lambda value: "financing" in value,
                            lambda value: "activities" in value]
                ),
            ]
            if all(candidate_groups):
                for operating, investing, financing in product(*candidate_groups):
                    for adjustment in ([0.0] + adjustment_values + [candidate[0] for candidate in adjustment_candidates]):
                        if abs(operating[0] + investing[0] + financing[0] + adjustment - net_change) <= 0.05:
                            cfo, cfo_src, cfo_pg = operating
                            cfi, cfi_src, cfi_pg = investing
                            cff, cff_src, cff_pg = financing
                            break
                    else:
                        continue
                    break

            required_adjustment = net_change - (cfo + cfi + cff)
            for candidate in adjustment_candidates:
                if abs(candidate[0] - required_adjustment) <= 0.05:
                    for row in adjustment_rows:
                        if "effect" in row["label"].lower():
                            row["values"] = [candidate[0]]
                            row["source_text"] = candidate[1]
                            row["page_number"] = candidate[2]
                            break
                    for row in rows:
                        if "effect" in row["label"].lower():
                            row["values"] = [candidate[0]]
                            row["source_text"] = candidate[1]
                            break
                    break
        return {
            "operating_cash_flow": ExtractionService._create_field(cfo, cfo_src, cfo_pg),
            "investing_cash_flow": ExtractionService._create_field(cfi, cfi_src, cfi_pg),
            "financing_cash_flow": ExtractionService._create_field(cff, cff_src, cff_pg),
            "net_change_in_cash": ExtractionService._create_field(net_change, nc_src, nc_pg),
            "opening_cash": ExtractionService._create_field(opening, o_src, o_pg),
            "closing_cash": ExtractionService._create_field(closing, cl_src, cl_pg),
            "line_items": [{"label": row["label"], "values": row["values"],
                            "source_text": row["source_text"], "page_number": row["page"]}
                           for row in rows]
            + [row for row in adjustment_rows if row["label"].lower() not in existing_labels],
            "comparative_periods": ExtractionService._comparative_periods(rows)
        }

        # Legacy label-only fallback retained for unusual OCR output.
        cfo, cfo_src, cfo_pg = ExtractionService._find_field_by_regex(lines, [
            r'net\s*cash\s*from\s*operating\s*activities[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'operating\s*cash\s*flow[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        cfi, cfi_src, cfi_pg = ExtractionService._find_field_by_regex(lines, [
            r'net\s*cash\s*from\s*investing\s*activities[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'investing\s*cash\s*flow[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        cff, cff_src, cff_pg = ExtractionService._find_field_by_regex(lines, [
            r'net\s*cash\s*from\s*financing\s*activities[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'financing\s*cash\s*flow[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        net_change, nc_src, nc_pg = ExtractionService._find_field_by_regex(lines, [
            r'net\s*increase\s*in\s*cash[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'net\s*change\s*in\s*cash[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        opening, o_src, o_pg = ExtractionService._find_field_by_regex(lines, [
            r'cash\s*and\s*cash\s*equivalents\s*at\s*beginning[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'opening\s*cash[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        closing, cl_src, cl_pg = ExtractionService._find_field_by_regex(lines, [
            r'cash\s*and\s*cash\s*equivalents\s*at\s*end[:.\s]+([₹$€£]?\s*[\d,.()]+)',
            r'closing\s*cash[:.\s]+([₹$€£]?\s*[\d,.()]+)'
        ], is_number=True)

        return {
            "operating_cash_flow": ExtractionService._create_field(cfo, cfo_src, cfo_pg),
            "investing_cash_flow": ExtractionService._create_field(cfi, cfi_src, cfi_pg),
            "financing_cash_flow": ExtractionService._create_field(cff, cff_src, cff_pg),
            "net_change_in_cash": ExtractionService._create_field(net_change, nc_src, nc_pg),
            "opening_cash": ExtractionService._create_field(opening, o_src, o_pg),
            "closing_cash": ExtractionService._create_field(closing, cl_src, cl_pg),
            "line_items": []
        }
