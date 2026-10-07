import os
import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import JobStatus, CertificateStatus
from app.services import process_job_batch

# Setup dedicated in-memory SQLite database for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# 1. Test Input Validation
def test_input_validation_empty_recipients(client):
    """Ensure submission fails when recipient list is empty."""
    payload = {
        "event_name": "AI Workshop",
        "issuer_name": "Tech Corp",
        "recipients": []
    }
    response = client.post("/api/certificates/generate", json=payload)
    assert response.status_code == 422  # Unprocessable Entity

def test_input_validation_invalid_email(client):
    """Ensure submission fails when any recipient email is malformed."""
    payload = {
        "event_name": "AI Workshop",
        "issuer_name": "Tech Corp",
        "recipients": [
            {"name": "Valid User", "email": "valid@example.com"},
            {"name": "Invalid User", "email": "not-an-email"}
        ]
    }
    response = client.post("/api/certificates/generate", json=payload)
    assert response.status_code == 422

def test_input_validation_blank_name(client):
    """Ensure submission fails when recipient name is blank."""
    payload = {
        "event_name": "AI Workshop",
        "issuer_name": "Tech Corp",
        "recipients": [
            {"name": "   ", "email": "user@example.com"}
        ]
    }
    response = client.post("/api/certificates/generate", json=payload)
    assert response.status_code == 422


# 2. Test Creating Generation Job
def test_create_generation_job(client):
    """Test job creation endpoint accepts valid payload and queues task."""
    payload = {
        "event_name": "Python Mastery",
        "issuer_name": "Code Academy",
        "issuer_title": "Lead Instructor",
        "custom_message": "for exemplary performance",
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"}
        ]
    }
    response = client.post("/api/certificates/generate", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["total_recipients"] == 2
    assert data["status"] == "PENDING"


# 3. Test Certificate Generation and Job Status/Progress
def test_certificate_generation_and_status(client, db_session):
    """Test full execution of background generator and status reporting."""
    payload = {
        "event_name": "Cloud Architecture Summit",
        "issue_date": "2026-10-07",
        "issuer_name": "Cloud Guild",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Martin", "email": "bob@example.com"}
        ]
    }
    res = client.post("/api/certificates/generate", json=payload)
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    # Directly run batch processing with our test session factory
    process_job_batch(job_id, TestingSessionLocal)

    # Check status endpoint
    status_res = client.get(f"/api/jobs/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()

    assert status_data["status"] == "COMPLETED"
    assert status_data["total_recipients"] == 2
    assert status_data["successful_count"] == 2
    assert status_data["failed_count"] == 0
    assert status_data["progress_percentage"] == 100.0
    assert len(status_data["certificates"]) == 2

    for cert in status_data["certificates"]:
        assert cert["status"] == "SUCCESS"
        assert cert["download_url"] is not None
        assert cert["certificate_code"].startswith("CERT-")


# 4. Test Handling Individual Certificate Failure (Partial Completion)
def test_individual_certificate_failure_isolation(client, db_session):
    """
    Ensure a single failing certificate does not break or cancel other certificates.
    Uses the [TEST_FAIL] simulation hook.
    """
    payload = {
        "event_name": "Resilience Testing Workshop",
        "issuer_name": "QA Guild",
        "recipients": [
            {"name": "Pass Recipient 1", "email": "pass1@example.com"},
            {"name": "Failing Recipient [TEST_FAIL]", "email": "fail@example.com"},
            {"name": "Pass Recipient 2", "email": "pass2@example.com"}
        ]
    }
    res = client.post("/api/certificates/generate", json=payload)
    job_id = res.json()["job_id"]

    process_job_batch(job_id, TestingSessionLocal)

    status_res = client.get(f"/api/jobs/{job_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()

    assert status_data["status"] == "PARTIALLY_COMPLETED"
    assert status_data["total_recipients"] == 3
    assert status_data["successful_count"] == 2
    assert status_data["failed_count"] == 1

    # Verify individual statuses
    certs = status_data["certificates"]
    failed_certs = [c for c in certs if c["status"] == "FAILED"]
    success_certs = [c for c in certs if c["status"] == "SUCCESS"]

    assert len(failed_certs) == 1
    assert "Simulated generation failure" in failed_certs[0]["error_message"]
    assert len(success_certs) == 2


# 5. Test Retrieving Generated Certificates (Single PDF and ZIP bundle)
def test_retrieve_certificates(client):
    """Test downloading individual PDF and batch ZIP archive."""
    payload = {
        "event_name": "Docker Mastery",
        "issuer_name": "DevOps Hub",
        "recipients": [
            {"name": "Charlie Brown", "email": "charlie@example.com"}
        ]
    }
    res = client.post("/api/certificates/generate", json=payload)
    job_id = res.json()["job_id"]

    process_job_batch(job_id, TestingSessionLocal)

    status_res = client.get(f"/api/jobs/{job_id}")
    cert_id = status_res.json()["certificates"][0]["id"]

    # 5.1 Test Single PDF download
    pdf_res = client.get(f"/api/certificates/{cert_id}/download")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000  # valid PDF binary

    # 5.2 Test Batch ZIP download
    zip_res = client.get(f"/api/jobs/{job_id}/download-zip")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    # Verify valid ZIP content
    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as zf:
        namelist = zf.namelist()
        assert len(namelist) == 1
        assert namelist[0].endswith(".pdf")


# 6. Test Non-existent Resources Return 404
def test_not_found_endpoints(client):
    res_job = client.get("/api/jobs/non-existent-id")
    assert res_job.status_code == 404

    res_cert = client.get("/api/certificates/non-existent-id/download")
    assert res_cert.status_code == 404
