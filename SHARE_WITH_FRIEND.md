# Document Intelligence Assignment - Complete Handoff

This folder is the complete working package for the project owner. It includes:

- `Neostats/` - the application source code, tests, documentation, Docker setup, and presentation.
- `New Dataset/` - the 50 supplied evaluation documents.
- `AI_Engineer_Internship_Case_Study_Document_Intelligence_Final_Revised 2 (1) (1).pdf` - the assignment document.

## Project status

The NeoStats application has been verified locally:

- Balance Sheet: 10/10 PASS
- Cash Flow: 10/10 PASS
- Profit & Loss: 10/10 PASS
- Invoice: 20/20 PASS
- Total supplied dataset: 50/50 PASS
- Automated tests: 12 passed
- Swagger: `/docs`
- Health endpoint: `/api/v1/health`
- Document list endpoint: `/api/v1/documents`

## Start here

Open `Neostats/HANDOFF.md` first, then read:

1. `Neostats/README.md`
2. `Neostats/SUBMISSION_CHECKLIST.md`
3. `Neostats/PRESENTATION_OUTLINE.md`
4. `Neostats/Neostats_Document_Intelligence_Presentation.pptx`

## Local setup

Open a terminal in `Neostats`:

```powershell
cd backend
python -m pip install -r requirements.txt
$env:PYTHONPATH="."
python -m pytest -q
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

In a second terminal:

```powershell
cd Neostats
python -m http.server 8001
```

Open `http://127.0.0.1:8001`.

Tesseract OCR must also be installed. On Windows, the usual path is:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Remaining work

The remaining work requires the owner's GitHub and hosting accounts:

- Push this assignment folder or the `Neostats` project to GitHub.
- Deploy the backend and frontend.
- Verify Tesseract OCR in the cloud environment.
- Replace local SQLite with persistent production storage if required.
- Add real repository, frontend, API, and Swagger URLs to the README.
- Submit the generated PPTX.

## Important sharing instructions

- Share this entire `document-intelligence-assignment` folder.
- Do not share the unrelated old CloudApp folder unless specifically needed.
- Do not share `.env` files, passwords, tokens, or deployment credentials.
- The chat itself may not transfer between Copilot accounts. This document contains the technical context needed to continue.
- The assignment PDF and `New Dataset` are included so the work can be reviewed and tested independently.

## Suggested first Copilot prompt

```text
This is the project owner's existing AI Engineer Internship Document Intelligence assignment. Read SHARE_WITH_FRIEND.md and Neostats/HANDOFF.md first. Continue working on the existing implementation; do not start over and do not modify the old CloudApp project. Run the existing tests before making changes, preserve the 50/50 dataset result, and focus on the remaining GitHub, deployment, and submission requirements.
```
