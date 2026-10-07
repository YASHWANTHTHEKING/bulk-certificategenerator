# Bulk Certificate Generator API

A high-performance backend API built with **FastAPI**, **SQLAlchemy**, and **ReportLab** that accepts bulk certificate generation requests for multiple recipients, validates data, asynchronously generates elegant digital PDF certificates, tracks job execution progress, and enables single or bulk ZIP downloads.

---

## Features

- **Bulk Certificate Generation**: Accepts a single API request containing any number of recipient entries.
- **Asynchronous Background Processing**: Generates certificates in non-blocking background workers (`FastAPI BackgroundTasks`), keeping API response times near-instantaneous (`202 Accepted`).
- **Input Validation**: Rigorous schema validation with Pydantic for recipient emails, non-empty names, and event details.
- **Fault Tolerance & Isolation**: Failure during generation of one certificate (e.g., corrupted font, invalid parameters) does not fail the batch. Each recipient is tracked individually with clear error logging.
- **Status & Progress Tracking**: Real-time percentage progress, counts of successful vs failed certificates, and detailed recipient records.
- **Certificate Retrieval**:
  - Individual PDF download by Certificate ID.
  - One-click bulk ZIP archive download for all certificates in a given job.
- **Predefined Certificate Template**: ReportLab canvas layout in landscape format featuring dual antique borders, decorative corner styling, verification IDs, and dynamic custom achievement text.
- **Automated Test Suite**: Pytest tests covering validation, creation, generation, progress tracking, failure isolation, and retrieval.

---

## Architecture & Technology Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Framework** | FastAPI | High async performance, automatic OpenAPI / Swagger UI docs, built-in background tasks. |
| **Database** | SQLite + SQLAlchemy ORM | Relational schema with foreign keys, transactional integrity, portable zero-config setup (easily swapped to PostgreSQL via `DATABASE_URL`). |
| **Data Validation** | Pydantic v2 | Strict validation of email format, non-empty text, and length limits. |
| **PDF Generation** | ReportLab | Fast, pure-Python vector PDF drawing without external heavy dependencies like WebKit or Chromium. |
| **Testing** | Pytest + FastAPI TestClient | In-memory SQLite testing with full branch and status verification. |

---

## Project Structure

```text
c:/yashwanthproject/
├── app/
│   ├── __init__.py
│   ├── config.py         # Configuration settings (environment variables, storage paths)
│   ├── database.py       # SQLAlchemy engine & session factory
│   ├── models.py         # Database models (GenerationJob, CertificateRecord)
│   ├── schemas.py        # Pydantic request/response schemas & validation
│   ├── generator.py      # ReportLab PDF template generation engine
│   ├── services.py       # Background worker & job orchestration logic
│   ├── routes.py         # REST API endpoints
│   └── main.py           # FastAPI entrypoint & lifespan events
├── tests/
│   ├── __init__.py
│   └── test_api.py       # Comprehensive pytest test suite
├── generated_certificates/ # File storage for generated PDFs
├── requirements.txt      # Python dependencies
├── demo.py               # End-to-end sample client script
└── README.md             # Documentation
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11)
- `pip`

### 2. Environment Setup

Clone or open the project folder, then set up a virtual environment:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Or Windows Command Prompt:
# .\venv\Scripts\activate.bat

# Install dependencies
python -m pip install -r requirements.txt
```

---

## Running the Application

Start the API server using Uvicorn:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Running the Tests

The test suite covers:
1. Input validation (empty recipient lists, invalid email formats, blank names)
2. Creating a generation job
3. Asynchronous certificate generation & job status/progress
4. Fault tolerance & individual certificate failure handling (`PARTIALLY_COMPLETED`)
5. Retrieving generated certificates (individual PDF & ZIP archive)
6. 404 handling for invalid IDs

Run the test suite with:

```powershell
.\venv\Scripts\python.exe -m pytest -v tests/
```

---

## API Usage Guide

### 1. Submit a Certificate Generation Request

- **Endpoint**: `POST /api/certificates/generate`
- **Status Code**: `202 Accepted`

#### Example Request:
```bash
curl -X POST "http://127.0.0.1:8000/api/certificates/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Full Stack & Cloud Architecture Masterclass",
    "issue_date": "2026-10-07",
    "issuer_name": "Global Tech Institute",
    "issuer_title": "Dean of Engineering",
    "custom_message": "for successfully completing the comprehensive 12-week program with distinction.",
    "recipients": [
      {
        "name": "Alice Johnson",
        "email": "alice.j@example.com"
      },
      {
        "name": "Bob Smith",
        "email": "bob.s@example.com"
      }
    ]
  }'
```

#### Example Response:
```json
{
  "job_id": "27f0980f-90eb-4342-a29d-434e7fcfef0e",
  "status": "PENDING",
  "total_recipients": 2,
  "message": "Certificate generation job accepted and processing in the background."
}
```

---

### 2. Check Job Status & Progress

- **Endpoint**: `GET /api/jobs/{job_id}`
- **Query Parameter**: `include_certificates` (boolean, default: `true`)

#### Example Request:
```bash
curl -X GET "http://127.0.0.1:8000/api/jobs/27f0980f-90eb-4342-a29d-434e7fcfef0e"
```

#### Example Response:
```json
{
  "job_id": "27f0980f-90eb-4342-a29d-434e7fcfef0e",
  "event_name": "Full Stack & Cloud Architecture Masterclass",
  "issuer_name": "Global Tech Institute",
  "status": "COMPLETED",
  "total_recipients": 2,
  "successful_count": 2,
  "failed_count": 0,
  "progress_percentage": 100.0,
  "created_at": "2026-10-07T17:35:00.000000",
  "updated_at": "2026-10-07T17:35:02.000000",
  "certificates": [
    {
      "id": "e6744bd7-10f7-41a0-b5bc-01d7ee3d537b",
      "recipient_name": "Alice Johnson",
      "recipient_email": "alice.j@example.com",
      "certificate_code": "CERT-8D4FA312",
      "status": "SUCCESS",
      "error_message": null,
      "download_url": "/api/certificates/e6744bd7-10f7-41a0-b5bc-01d7ee3d537b/download",
      "created_at": "2026-10-07T17:35:00.000000",
      "updated_at": "2026-10-07T17:35:01.000000"
    },
    {
      "id": "18f5cc02-f327-46f9-b4cf-70bc1b9dbd46",
      "recipient_name": "Bob Smith",
      "recipient_email": "bob.s@example.com",
      "certificate_code": "CERT-2A8E5C41",
      "status": "SUCCESS",
      "error_message": null,
      "download_url": "/api/certificates/18f5cc02-f327-46f9-b4cf-70bc1b9dbd46/download",
      "created_at": "2026-10-07T17:35:00.000000",
      "updated_at": "2026-10-07T17:35:02.000000"
    }
  ]
}
```

---

### 3. Retrieve Individual Certificate PDF

- **Endpoint**: `GET /api/certificates/{cert_id}/download`

```bash
curl -O -J "http://127.0.0.1:8000/api/certificates/e6744bd7-10f7-41a0-b5bc-01d7ee3d537b/download"
```
Downloads the generated PDF file directly (e.g. `CERT-8D4FA312_Alice_Johnson.pdf`).

---

### 4. Retrieve All Certificates in a ZIP Archive

- **Endpoint**: `GET /api/jobs/{job_id}/download-zip`

```bash
curl -O -J "http://127.0.0.1:8000/api/jobs/27f0980f-90eb-4342-a29d-434e7fcfef0e/download-zip"
```
Bundles and streams all successfully generated certificates into a single `.zip` archive.

---

### 5. List All Jobs

- **Endpoint**: `GET /api/jobs?limit=20&offset=0`

Returns paginated list of all created jobs with their status and progress metrics.

---

## Design Decisions & Technical Rationale

1. **FastAPI & Async Background Tasks**:
   - Bulk certificate generation is I/O and CPU intensive. Handling requests synchronously would lead to HTTP timeouts for requests with hundreds or thousands of recipients.
   - Returning `202 Accepted` immediately gives callers a `job_id` to poll or link to frontend progress indicators.

2. **Per-Certificate Fault Isolation**:
   - The worker loops through recipients in an isolated `try...except` block.
   - If one recipient generation throws an error (e.g. unexpected character rendering, file lock issue), that individual certificate is flagged as `FAILED` with its `error_message` stored, while remaining recipients continue processing.
   - The job ends in `PARTIALLY_COMPLETED` if some succeeded and some failed, or `COMPLETED` if all succeeded.

3. **ReportLab over Headless Browser (Puppeteer/Playwright)**:
   - ReportLab produces native vector PDFs with tiny file sizes (~3KB per certificate) and sub-millisecond generation speed per certificate.
   - It requires no browser binaries or Node.js runtime, ensuring minimal dependencies and maximum portability across hosting environments.

4. **Batch ZIP Streaming**:
   - The `/download-zip` endpoint uses `io.BytesIO` and `StreamingResponse` to zip existing generated files on demand without leaving lingering temp files on disk.

5. **Relational Schema**:
   - Foreign-key linked tables `generation_jobs` and `certificates` provide strong relational integrity, fast queries on status, and support for indexing unique verification codes.
