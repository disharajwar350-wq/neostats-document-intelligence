import re
from typing import Any

from app.schemas.document import Evidence, ExtractedValue


FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "invoice_number": ("invoice number", "invoice no", "invoice #", "inv no"),
    "invoice_date": ("invoice date", "date"),
    "vendor_name": ("vendor name", "vendor", "supplier", "seller"),
    "customer_name": ("customer name", "customer", "bill to", "buyer"),
    "currency": ("currency",),
    "subtotal": ("subtotal", "sub total", "taxable amount"),
    "tax_amount": ("sales tax", "tax amount", "gst", "vat", "tax"),
    "discount": ("discount",),
    "shipping_and_handling": ("shipping & handling", "shipping and handling", "shipping"),
    "total_amount": ("total due", "amount due", "grand total", "total amount"),
    "total_assets": ("total assets",),
    "total_liabilities": ("total liabilities", "total liabilities and equity"),
    "total_equity": ("total equity", "shareholders equity", "owners equity"),
    "revenue": ("revenue", "total revenue", "sales"),
    "cost_of_sales": ("cost of sales", "cost of goods sold", "cogs"),
    "gross_profit": ("gross profit",),
    "operating_expenses": ("operating expenses",),
    "operating_profit": ("operating profit", "operating income"),
    "tax": ("tax", "income tax"),
    "net_profit": ("net profit", "net income", "profit for the year"),
    "operating_cash_flow": ("operating cash flow", "net cash flow from operating activities"),
    "investing_cash_flow": ("investing cash flow", "net cash flow from investing activities"),
    "financing_cash_flow": ("financing cash flow", "net cash flow from financing activities"),
    "opening_cash": ("opening cash", "cash at beginning"),
    "net_change_in_cash": ("net change in cash", "net increase in cash"),
    "closing_cash": ("closing cash", "cash at end"),
}

NUMERIC_FIELDS = {
    key for key in FIELD_ALIASES
    if key not in {"invoice_number", "invoice_date", "vendor_name", "customer_name", "currency"}
}


def _number(raw: str) -> float | None:
    cleaned = raw.replace(",", "").replace("$", "").replace("€", "").replace("£", "")
    match = re.search(r"\(?\s*-?\d+(?:\.\d+)?\s*\)?", cleaned)
    if not match:
        return None
    token = match.group(0).strip()
    negative = token.startswith("(") and token.endswith(")")
    value = float(token.strip("() "))
    return -abs(value) if negative else value


def _is_numeric_line(value: str) -> bool:
    return re.fullmatch(r"\(?\s*-?\d+(?:,\d{3})*(?:\.\d+)?\s*\)?", value) is not None


def _evidence(text: str, pages: list[str], match: re.Match[str]) -> dict[str, Any]:
    source = match.group(0).strip()
    page_number = next((i + 1 for i, page in enumerate(pages) if source in page), None)
    return Evidence(source_text=source, page_number=page_number).model_dump()


def _value(raw: str, text: str, pages: list[str], match: re.Match[str], numeric: bool) -> dict:
    value = _number(raw) if numeric else raw.strip()
    return ExtractedValue(value=value, evidence=_evidence(text, pages, match)).model_dump()


def extract_structured(text: str, pages: list[str], document_type: str) -> dict[str, Any]:
    data: dict[str, Any] = {"raw_text": text}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for field, aliases in FIELD_ALIASES.items():
        aliases_pattern = "|".join(re.escape(alias) for alias in aliases)
        match = re.search(rf"(?im)^\s*(?:{aliases_pattern})\s*[:#-]?\s*(.+?)\s*$", text)
        if not match:
            for line_index, line in enumerate(lines[:-1]):
                if any(line.casefold() == alias.casefold() for alias in aliases):
                    next_line = lines[line_index + 1]
                    if field in NUMERIC_FIELDS and _number(next_line) is not None:
                        match = re.search(re.escape(line) + r"\s*\n\s*" + re.escape(next_line), text, re.I)
                        if match:
                            data[field] = _value(next_line, text, pages, match, True)
                    break
        if match:
            if field not in data:
                data[field] = _value(match.group(1), text, pages, match, field in NUMERIC_FIELDS)
        else:
            data[field] = ExtractedValue(value=None).model_dump()

    if document_type == "invoice":
        invoice_index = next((i for i, line in enumerate(lines) if line.upper() == "INVOICE"), 0)
        vendor = next((line for line in lines[:invoice_index]
                       if line and not line.lower().startswith(("phone:", "date:"))), None)
        data["vendor_name"] = _named_value(vendor, text, pages)
        customer = _section_value(lines, "TO:", ("SHIP TO:", "COMMENTS"))
        customer_value = customer.get("value")
        data["customer_name"] = _named_value(customer_value, text, pages)
        data["line_items"] = extract_line_items(text)
    else:
        data["line_items"] = []
    return data


def _section_value(lines: list[str], start: str, ends: tuple[str, ...]) -> dict:
    try:
        start_index = next(i for i, line in enumerate(lines) if line.upper() == start.upper())
    except StopIteration:
        return ExtractedValue(value=None).model_dump()
    for index in range(start_index + 1, len(lines)):
        upper = lines[index].upper()
        if any(upper.startswith(end) for end in ends):
            break
        if len(lines[index]) > 2 and not upper.startswith(("PHONE:", "DATE:", "INVOICE")):
            return ExtractedValue(value=lines[index]).model_dump()
    return ExtractedValue(value=None).model_dump()


def _named_value(value: str | None, text: str, pages: list[str]) -> dict:
    if not value:
        return ExtractedValue(value=None).model_dump()
    page_number = next((i + 1 for i, page in enumerate(pages) if value in page), None)
    return ExtractedValue(
        value=value,
        evidence=Evidence(source_text=value, page_number=page_number).model_dump(),
    ).model_dump()


def extract_line_items(text: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    single_line = re.compile(
        r"(?im)^\s*(.+?)\s+(\d+(?:\.\d+)?)\s+([\d,]+(?:\.\d+)?)\s+([\d,]+(?:\.\d+)?)\s*$"
    )
    for match in single_line.finditer(text):
        items.append({
            "description": match.group(1).strip(),
            "quantity": float(match.group(2)),
            "unit_price": float(match.group(3).replace(",", "")),
            "amount": float(match.group(4).replace(",", "")),
        })
    if items:
        return items
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    start = next((i for i, line in enumerate(lines) if line.upper() == "QUANTITY"), None)
    end = next((i for i, line in enumerate(lines[start + 1:], start + 1)
                if line.upper() == "SUBTOTAL"), len(lines)) if start is not None else 0
    index = (start or 0) + 1
    while index < end:
        quantity_match = re.fullmatch(r"\d+(?:\.\d+)?", lines[index])
        if not quantity_match:
            index += 1
            continue
        quantity = float(lines[index])
        if index + 3 >= end:
            break
        description = lines[index + 1]
        candidate = lines[index + 2:index + 5]
        if len(candidate) == 3 and not _is_numeric_line(candidate[0]):
            unit_price = _number(candidate[1])
            amount = _number(candidate[2])
            next_index = index + 5
        else:
            unit_price = _number(candidate[0])
            amount = _number(candidate[1]) if len(candidate) > 1 else None
            next_index = index + 4
        if unit_price is None or amount is None:
            next_index = index + 1
        if unit_price is not None and amount is not None:
            items.append({
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
            })
        index = next_index
    return items
