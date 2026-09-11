# 📊 NeoStats — Financial Document Extraction Engine

> Transform raw OCR text from financial documents into clean, structured JSON with full provenance tracking.

![Status](https://img.shields.io/badge/Status-Local_Verified-06d6a0?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-00b4d8?style=flat-square)
![Dependencies](https://img.shields.io/badge/Dependencies-Python%20%2B%20Tesseract-7b61ff?style=flat-square)

---

## ✨ Features

- **🔍 Smart Field Matching** — Fuzzy label matching against 100+ field aliases to handle OCR variations
- **📅 Multi-Period Detection** — Automatically detects multiple fiscal periods (e.g., "31-Mar-24", "FY2024")
- **🔢 Number Normalization** — Handles commas (1,234,567), parenthetical negatives (500) → -500, currency symbols (₹, $, €)
- **📝 Source Provenance** — Every extracted value includes the exact OCR source line and page number
- **✅ Built-in Validation** — Validates required fields, numeric types, and source text presence
- **📤 Export Options** — Download as JSON or CSV
- **🎨 Premium Dark UI** — Glassmorphism design with smooth animations
- **⌨️ Keyboard Shortcuts** — Ctrl+Enter to extract
- **📁 Drag & Drop** — Drop OCR text files directly onto the UI
- **🚫 No API Keys** — The browser demo has no external service dependency

---

## 🏗️ Architecture

NeoStats has two complementary surfaces: the browser UI is a dependency-free OCR-text
demonstration, while the FastAPI service in `backend/` performs PDF/JPG/PNG ingestion,
Tesseract OCR, evidence-grounded extraction, validation, and SQLite persistence.

```
NeoStats/
├── index.html              ← Main web UI
├── css/
│   └── style.css           ← Design system (dark mode, glassmorphism)
├── js/
│   ├── normalizer.js       ← Number cleaning (commas, parens, currency)
│   ├── parser.js           ← OCR text → structured lines & periods
│   ├── schemas.js          ← Field definitions & aliases per doc type
│   ├── validator.js        ← Output JSON validation
│   ├── extractor.js        ← Main extraction orchestrator
│   └── app.js              ← UI controller & event handling
├── samples/
│   ├── balance_sheet.txt   ← Sample OCR data
│   ├── income_statement.txt
│   └── cash_flow.txt
├── backend/               ← FastAPI OCR and document-processing service
└── README.md              ← You are here
```

### Data Flow

```
OCR Text → Parser → Line Splitting → Period Detection
                  → Data Row Parsing → Label Extraction
                  → Field Matching (fuzzy alias match)
                  → Number Normalization
                  → Output Assembly (periods × fields)
                  → Validation → Structured JSON
```

---

## 🚀 Quick Start

### Option 1: Open Directly
Simply open `index.html` in your browser. That's it!

### Option 2: Local Server (recommended for file loading)
```bash
# Using Python
python -m http.server 8000

# Using Node.js
npx serve .

# Using PHP
php -S localhost:8000
```

Then visit `http://localhost:8000`

### Backend API

```bash
cd Neostats
pip install -r backend/requirements.txt
$env:PYTHONPATH="."
uvicorn backend.app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

### Docker

```bash
docker build -t neostats .
docker run --rm -p 8000:8000 -e NEOSTATS_CORS_ORIGINS=http://localhost:8000 neostats
```

The image installs Linux Tesseract automatically and uses `/usr/bin/tesseract`.

The dashboard upload flow uses the same API. Select a document type, upload a PDF/JPG/PNG,
and click **Extract Data**. The browser displays the backend JSON, evidence lines, line
items, validation checks, and lets you download the result as JSON or CSV. For a separate
frontend origin, set `NEOSTATS_CORS_ORIGINS` to a comma-separated allowlist.

Example API request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/process \
  -F "document_type=Invoice" \
  -F "file=@invoice.jpg"
```

---

## 📋 Supported Document Types

### 1. Balance Sheet
Extracts: Total Assets, Current Assets, Fixed Assets, Inventories, Trade Receivables, Cash & Equivalents, Total Liabilities, Current Liabilities, Borrowings, Trade Payables, Shareholders' Equity, Share Capital, Reserves & Surplus, and more.

### 2. Income Statement (P&L)
Extracts: Revenue, Other Income, COGS, Employee Expenses, Depreciation, Finance Costs, Gross Profit, Operating Profit, EBITDA, Profit Before Tax, Tax Expense, Net Profit, Basic EPS, Diluted EPS, and more.

### 3. Cash Flow Statement
Extracts: Cash from Operations, Cash from Investing, Cash from Financing, CapEx, Dividends Paid, Borrowings Raised/Repaid, Net Change in Cash, Opening/Closing Cash, and more.

### 4. Invoice
Extracts invoice identity, parties, subtotal, tax, shipping, discount, total due, and
line-item evidence when those values are visible in the source.

---

## 📊 Output JSON Schema

```json
{
  "document_type": "Balance Sheet",
  "extraction_timestamp": "2024-03-15T10:30:00.000Z",
  "periods_detected": ["31-Mar-24", "31-Mar-23"],
  "periods": {
    "31-Mar-24": {
      "total_assets": {
        "value": "12247.70",
        "raw_value": "12,247.70",
        "source_text": "Total Assets                12,247.70   10,962.55",
        "page": 1,
        "field_name": "total_assets",
        "category": "Assets"
      }
    }
  },
  "line_items": [...],
  "metadata": {
    "total_lines_parsed": 35,
    "fields_matched": 15,
    "fields_total": 22,
    "extraction_rate": "68.2%"
  },
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "stats": { "extractedFields": 30, "totalFields": 44, "extractionRate": "68.2%" }
  }
}
```

---

## 🔧 Extraction Rules

1. **ONLY extract values explicitly present** in the OCR text. Missing fields → `null`.
2. **Preserve numbers exactly** after removing thousands separators.
3. **Convert parenthetical negatives**: `(500)` → `-500`
4. **Multi-period support**: Each period gets its own key in the `periods` object.
5. **Source provenance**: Every value includes `source_text` and `page`.
6. **Never estimate or infer** — if not confident, value is `null`.

---

## 🧩 Extending

### Adding a New Document Type

1. Open `js/schemas.js`
2. Add a new schema object following the pattern:

```javascript
const MY_NEW_TYPE = {
    documentType: 'My New Type',
    fields: [
        {
            name: 'field_name',           // Canonical name in output
            aliases: ['alias1', 'alias2'], // OCR label variations
            type: 'number',               // 'number' | 'string' | 'date'
            required: true,               // Required in output?
            category: 'Category Name'     // For grouping
        },
        // ... more fields
    ]
};
```

3. Update `getSchema()` to recognize the new type
4. Add the option to the `<select>` in `index.html`

### Adding Field Aliases

If the extractor misses a field because the OCR label is different, simply add the new alias to the field's `aliases` array in `schemas.js`.

---

## 🧪 Testing

Load the included sample files via the "Quick Load Sample" buttons in the UI, or paste them manually. Expected results:

| Document Type | Sample File | Expected Fields | Periods |
|---|---|---|---|
| Balance Sheet | `samples/balance_sheet.txt` | 20+ fields | 31-Mar-24, 31-Mar-23 |
| Income Statement | `samples/income_statement.txt` | 15+ fields | 31-Mar-24, 31-Mar-23 |
| Cash Flow Statement | `samples/cash_flow.txt` | 15+ fields | 31-Mar-24, 31-Mar-23 |

The supplied evaluation dataset contains 50 files. The Tesseract-enabled
verification run completed all 50 files successfully: 10 balance sheets, 10
cash-flow statements, 10 P&L statements, and 20 invoices. The verification used
`TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`. The source values
and validation variances remain visible in the results.

### Production deployment notes

- Install the Tesseract OCR system package on the host; Python `pytesseract` alone is not
  sufficient. The Windows fallback path is `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- Configure `NEOSTATS_CORS_ORIGINS` with the deployed frontend origin instead of using
  the development wildcard.
- Use persistent storage for SQLite or replace it with a managed database before running
  multiple production instances.
- Enforce HTTPS and configure the platform's file-size/time-out limits for OCR workloads.

### Submission status

The local implementation and presentation are complete and verified. The following
deliverables still require external account access: a public GitHub repository, live
frontend/API deployment, deployed Swagger and health URLs, and production
database/OCR verification. Do not replace these placeholders with invented URLs:

| Deliverable | URL |
|---|---|
| Public GitHub repository | Pending publication |
| Frontend | Pending deployment |
| Backend API | Pending deployment |
| Swagger/OpenAPI | Pending deployment |

### AI/tool usage disclosure

GitHub Copilot (Copilot SDK in VS Code) was used for repository inspection,
implementation assistance, test execution, documentation, and presentation drafting.
No third-party LLM or paid OCR API is required at runtime; OCR uses local Tesseract.

---

## 🛡️ Privacy

The browser demo processes pasted OCR text locally. The optional FastAPI backend processes
uploaded documents locally and stores result metadata in SQLite; no third-party OCR API is used. Your financial documents stay on your machine.

---

## 📄 License

MIT License — Use freely for personal and commercial projects.
