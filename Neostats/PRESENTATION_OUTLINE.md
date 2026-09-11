# NeoStats Presentation Outline

## 1. Problem and objective

Financial PDFs and invoice images vary in layout and OCR quality. NeoStats validates,
extracts, grounds, stores, and exposes the results through a dashboard and REST API.

## 2. Architecture

`Upload -> file validation -> native text/OCR -> schema-aware extraction -> evidence ->
financial validation -> SQLite persistence -> dashboard/API`

## 3. Technology choices

- FastAPI: typed multipart REST API and Swagger.
- PyMuPDF/pypdf: native PDF reading and page rendering.
- Tesseract/pytesseract: local OCR for scanned PDFs and images.
- SQLite: simple persistent assignment datastore.
- HTML/CSS/JavaScript: deployable lightweight frontend.

## 4. Supported document types

Invoice, Balance Sheet, Profit & Loss, and Cash Flow Statement.

## 5. Validation examples

- Invoice: subtotal + tax + shipping - discount = total.
- Balance sheet: liabilities + equity = assets.
- P&L: revenue/expense/profit checks when fields are present.
- Cash flow: operating + investing + financing + adjustments = net change and
  opening + net change = closing.

## 6. Evidence and failure handling

Each extracted field includes source text and page number where available. Missing
values are null, unsupported/corrupt files return controlled errors, and unavailable
financial checks return `NOT_APPLICABLE`.

## 7. Verification

The supplied dataset contains 50 documents. The verified result is 10/10 for each:
Balance Sheet, Cash Flows, Profit & Loss, and Invoices. The automated suite passes 12 tests.

## 8. Demonstration flow

Select a document type, upload a PDF/JPG/PNG, process it, open the JSON/evidence/line-item
tabs, inspect validation checks, download JSON, and reopen the result from Processing History.

## 9. Limitations and next steps

Comparative values can be retained in line items but need a fully period-keyed canonical
schema. Public deployment, repository URL, and persistent production storage are final
submission operations.
