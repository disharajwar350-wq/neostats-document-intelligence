from app.services.schema_extractor import extract_structured


def test_extracts_values_evidence_and_invoice_line_item():
    text = (
        "Invoice Number: INV-7\n"
        "Currency: USD\n"
        "Subtotal: 100.00\n"
        "Tax Amount: 5.00\n"
        "Total Amount: 105.00\n"
        "Service A 2 50.00 100.00"
    )
    result = extract_structured(text, [text], "invoice")
    assert result["invoice_number"]["value"] == "INV-7"
    assert result["total_amount"]["evidence"]["page_number"] == 1
    assert result["line_items"][0]["amount"] == 100.0
    assert result["line_items"][0]["description"] == "Service A"


def test_extracts_multiline_invoice_totals_and_parties():
    text = (
        "Bioplex\nINVOICE\nINVOICE # BPX-1\nDATE: 23.05.2021\n"
        "TO:\nRoger Bigot\nSHIP TO:\nRoger Bigot\n"
        "QUANTITY\nDESCRIPTION\nUNIT PRICE\nTOTAL\n"
        "10\nDextromethorphan\nBPX-2\n12.45\n124.50\n"
        "SUBTOTAL\n5964.50\nSALES TAX\n596.45\n"
        "SHIPPING & HANDLING\n50.00\nTOTAL DUE\n6610.95"
    )
    result = extract_structured(text, [text], "invoice")
    assert result["vendor_name"]["value"] == "Bioplex"
    assert result["customer_name"]["value"] == "Roger Bigot"
    assert result["tax_amount"]["value"] == 596.45
    assert result["shipping_and_handling"]["value"] == 50.0
    assert result["total_amount"]["value"] == 6610.95
    assert result["line_items"][0]["amount"] == 124.5
    assert result["line_items"][0]["quantity"] == 10
