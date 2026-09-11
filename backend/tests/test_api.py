import io

import fitz
from fastapi.testclient import TestClient

from app.main import app


def _pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def test_process_invoice_and_retrieve_latest_result():
    client = TestClient(app)
    content = _pdf(
        "Invoice Number: INV-1\n"
        "Vendor Name: Example Vendor\n"
        "Subtotal: 100\nTax Amount: 10\nDiscount: 0\nTotal Amount: 110"
    )
    response = client.post(
        "/api/v1/documents/process",
        files={"file": ("api-invoice.pdf", io.BytesIO(content), "application/pdf")},
        data={"document_type": "invoice"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["validation"]["overall_status"] == "PASS"
    retrieved = client.get("/api/v1/documents/api-invoice.pdf")
    assert retrieved.status_code == 200
    assert retrieved.json()["document_name"] == "api-invoice.pdf"


def test_process_rejects_corrupt_pdf():
    client = TestClient(app)
    response = client.post(
        "/api/v1/documents/process",
        files={"file": ("broken.pdf", io.BytesIO(b"not a pdf"), "application/pdf")},
        data={"document_type": "invoice"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNREADABLE_FILE"
