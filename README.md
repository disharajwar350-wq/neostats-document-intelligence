# Document Intelligence Assignment

Separate implementation for the AI Engineer Internship case study. The original CloudApp project is intentionally not modified.

## Current scope

- FastAPI REST API with Swagger at `/docs`.
- PDF/JPG/PNG validation, including empty, unreadable, and three-page-limit checks.
- PyMuPDF native PDF extraction and Tesseract OCR fallback.
- Structured JSON response with evidence fields where text can be matched.
- SQLite persistence and latest-result lookup by document name.
- HTML/CSS/JavaScript dashboard.
- Schema-aware field extraction for invoice, balance sheet, profit and loss, and cash flow documents.
- Invoice, balance-sheet, profit-and-loss, and cash-flow reconciliation checks with `NOT_APPLICABLE` when required inputs are missing.
- Unit and API tests for validation, extraction flow, persistence, and controlled invalid-file errors.

The active implementation is in [`Neostats/`](./Neostats/). The deployed service
uses this directory as its Docker root.

## Local setup

```powershell
cd Neostats
python -m pip install -r backend/requirements.txt
$env:PYTHONPATH="."
python -m pytest -q
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000` for the dashboard and `http://127.0.0.1:8000/docs` for Swagger.

## Render deployment

The deployed application is available at:

- Frontend: https://neostats-document-intelligence-1.onrender.com/
- Backend API: https://neostats-document-intelligence-1.onrender.com/api/v1
- Swagger/OpenAPI: https://neostats-document-intelligence-1.onrender.com/docs
- Health: https://neostats-document-intelligence-1.onrender.com/api/v1/health

The included [render.yaml](./render.yaml) targets the active `Neostats` FastAPI
API and static frontend as one Docker web service.

## API

- `POST /api/v1/documents/process` multipart fields: `file`, `document_type`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_name}`
- `GET /api/v1/health`

## Submission contents

The repository contains the active application, automated tests, sample structured
output, environment template, Docker deployment configuration, and the mandatory
presentation. The public repository URL is:

https://github.com/disharajwar350-wq/neostats-document-intelligence
