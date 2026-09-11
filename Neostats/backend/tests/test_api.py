from fastapi.testclient import TestClient
import fitz
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_documents_endpoint():
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_process_invoice():
    sample_ocr = """
    ABC Technologies
    Invoice #: INV-9901
    Date: 2026-09-10
    Bill To: Global Client Corp
    Subtotal: $ 1,000.00
    Tax Amount: $ 100.00
    Discount: $ 50.00
    Total Amount: $ 1,050.00
    Software License 1 1000.00 1000.00
    """
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), sample_ocr)
    pdf_bytes = pdf.tobytes()
    pdf.close()
    response = client.post(
        "/api/v1/documents/process",
        data={"document_type": "invoice"},
        files={"file": ("sample_invoice.pdf", pdf_bytes, "application/pdf")}
    )
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["processing_status"] == "PASS"
    assert res_json["extracted_data"]["invoice_number"]["value"] == "INV-9901"
    assert res_json["validation"]["overall_status"] == "PASS"


def test_process_rejects_unsupported_extension():
    response = client.post(
        "/api/v1/documents/process",
        data={"document_type": "invoice"},
        files={"file": ("malware.exe", b"not a supported document", "application/octet-stream")}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_process_rejects_empty_pdf():
    response = client.post(
        "/api/v1/documents/process",
        data={"document_type": "invoice"},
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FILE_ERROR"
