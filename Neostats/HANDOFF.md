# NeoStats Project Handoff

## Project

NeoStats is a FastAPI + Tesseract + SQLite financial document intelligence application for the AI Engineer Internship assignment.

This is the owner's project. You are continuing work on it from this handoff.
Work inside this `Neostats` folder for the implementation. The older CloudApp
project is separate and should not be modified for this assignment.

## Supported documents

- Invoice
- Balance Sheet
- Profit & Loss
- Cash Flow

Supported input formats:

- PDF
- JPG/JPEG
- PNG

The backend supports native PDF text extraction, scanned PDF OCR, image OCR, structured extraction, evidence, financial validation, persistence, REST APIs, and dashboard history.

## Verified status

- Balance Sheet dataset: 10/10 PASS
- Cash Flow dataset: 10/10 PASS
- Profit & Loss dataset: 10/10 PASS
- Invoice dataset: 20/20 PASS
- Total supplied dataset: 50/50 PASS
- Automated tests: 12 passed
- Swagger route: `/docs`
- Health route: `/api/v1/health`
- Document list route: `/api/v1/documents`

## Read first

1. `README.md`
2. `SUBMISSION_CHECKLIST.md`
3. `PRESENTATION_OUTLINE.md`
4. `Neostats_Document_Intelligence_Presentation.pptx`
5. `backend/app/services/extraction_service.py`
6. `backend/app/services/financial_validation_service.py`
7. `backend/tests/`

## Local setup

From the `Neostats` folder:

```powershell
cd backend
python -m pip install -r requirements.txt
$env:PYTHONPATH="."
python -m pytest -q
uvicorn app.main:app --reload
```

Open the API documentation at `http://127.0.0.1:8000/docs`.

From a second terminal, serve the frontend:

```powershell
cd Neostats
python -m http.server 8001
```

Open `http://127.0.0.1:8001`.

Tesseract OCR must be installed locally. On Windows, the default executable path is:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

Use `TESSERACT_CMD` when the executable is installed elsewhere.

## Remaining external submission work

These items require repository or hosting access and are not local code defects:

- Push the project to a public GitHub repository.
- Deploy the backend and frontend.
- Configure and verify Tesseract on the hosting platform.
- Use persistent production storage instead of local SQLite.
- Add the real repository, frontend, API, and Swagger URLs to `README.md`.
- Submit the generated PPTX with the assignment.

## Safe collaboration rules

- Do not commit `.env` files or credentials.
- Do not commit private deployment secrets.
- Do not remove the supplied dataset or the test suite.
- Run `python -m pytest -q` after backend changes.
- Re-run the 50-file dataset check after changing extraction or validation logic.
- Prefer small, focused changes and document any behavior changes.

## Suggested first Copilot prompt

```text
Read HANDOFF.md, README.md, and SUBMISSION_CHECKLIST.md. Inspect the current NeoStats implementation and tests. Work only in this project, not the old CloudApp project. First verify the existing tests, then address the remaining submission or production-readiness work without weakening extraction, evidence, or validation behavior.
```
