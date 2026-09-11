# NeoStats Submission Checklist

This checklist maps the internship case-study requirements to the implementation.

## Implemented and verified locally

- Four selected document types: Invoice, Balance Sheet, Profit & Loss, Cash Flow.
- PDF/JPG/PNG validation, empty/corrupt-file handling, MIME/extension checks, and three-page limit.
- Native PDF text extraction and scanned PDF/image OCR through Tesseract.
- Structured extracted fields, line items, source text evidence, and page numbers.
- Invoice total, line-item, balance-sheet, P&L, and cash-flow validation results.
- `PASS`, `FAILED`, and `NOT_APPLICABLE` processing/validation states.
- Multipart upload API, latest-result retrieval, list API, and health API.
- Swagger/OpenAPI at `/docs`.
- SQLite persistence and dashboard processing history.
- Dashboard upload/process flow, JSON view, line-item view, evidence/validation details, and downloads.
- Automated regression tests for file validation, financial calculations, API flow, OCR-layout regressions, and tolerance handling.
- Complete supplied dataset verification: 50/50 successful with the installed
  Windows Tesseract executable.
- Submission presentation generated: `Neostats_Document_Intelligence_Presentation.pptx`.
- Sample structured output: `sample_outputs/invoice.json`.
- Architecture and processing flow: architecture slide in the submission PPTX.
- AI/tool usage disclosure is included in `README.md`.

## Remaining submission actions outside local implementation

- Deploy the Docker image or application to a public free-tier platform.
- Install/configure Tesseract on the hosting platform and verify the deployed OCR flow.
- Push the project to a public GitHub repository.
- Fill the deployed frontend, API, Swagger, and repository URLs in the README.
- Submit `Neostats_Document_Intelligence_Presentation.pptx` with the repository.

## Known non-blocking limitations

- Comparative values are exposed in the `comparative_periods` array with current and
  comparative values, source text, and page numbers for annual-report rows.
- SQLite is suitable for the assignment/demo but should use persistent storage in production.
