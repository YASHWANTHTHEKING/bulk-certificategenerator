import os
import uuid
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.config import settings
from app.models import GenerationJob, CertificateRecord, JobStatus, CertificateStatus
from app.schemas import CertificateJobCreateRequest
from app.generator import generate_certificate_pdf

logger = logging.getLogger(__name__)

def create_job(db: Session, request_data: CertificateJobCreateRequest) -> GenerationJob:
    """
    Creates the generation job and initial recipient certificate records in PENDING state.
    """
    job_id = str(uuid.uuid4())
    issue_date = request_data.issue_date or datetime.utcnow().strftime("%Y-%m-%d")
    
    job = GenerationJob(
        id=job_id,
        event_name=request_data.event_name,
        issue_date=issue_date,
        issuer_name=request_data.issuer_name,
        issuer_title=request_data.issuer_title,
        custom_message=request_data.custom_message,
        status=JobStatus.PENDING,
        total_recipients=len(request_data.recipients),
        successful_count=0,
        failed_count=0
    )
    db.add(job)

    # Pre-populate certificate records
    for recipient in request_data.recipients:
        cert_id = str(uuid.uuid4())
        short_code = f"CERT-{uuid.uuid4().hex[:8].upper()}"
        cert_record = CertificateRecord(
            id=cert_id,
            job_id=job_id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            certificate_code=short_code,
            status=CertificateStatus.PENDING
        )
        db.add(cert_record)

    db.commit()
    db.refresh(job)
    return job

def process_job_batch(job_id: str, db_session_factory):
    """
    Worker task running in background to process all certificates for the job.
    Uses its own db session to ensure thread-safety.
    Each certificate generation is isolated so a single failure does not abort the entire batch.
    """
    db: Session = db_session_factory()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found for processing.")
            return

        job.status = JobStatus.PROCESSING
        db.commit()

        # Job certificate output directory
        job_dir = os.path.join(settings.STORAGE_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        cert_records: List[CertificateRecord] = db.query(CertificateRecord).filter(
            CertificateRecord.job_id == job_id
        ).all()

        success_count = 0
        failed_count = 0

        for cert in cert_records:
            try:
                # Deliberate failure test hook: if recipient name contains "[TEST_FAIL]"
                if "[TEST_FAIL]" in cert.recipient_name:
                    raise ValueError(f"Simulated generation failure for recipient {cert.recipient_name}")

                filename = f"{cert.certificate_code}_{cert.recipient_name.replace(' ', '_')}.pdf"
                # Clean unsafe characters in filename
                safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
                file_path = os.path.join(job_dir, safe_filename)

                # Generate PDF
                generate_certificate_pdf(
                    file_path=file_path,
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    issue_date=job.issue_date,
                    issuer_name=job.issuer_name,
                    issuer_title=job.issuer_title,
                    custom_message=job.custom_message,
                    certificate_code=cert.certificate_code
                )

                cert.file_path = file_path
                cert.file_url = f"/api/certificates/{cert.id}/download"
                cert.status = CertificateStatus.SUCCESS
                cert.error_message = None
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to generate certificate {cert.id} for {cert.recipient_name}: {e}")
                cert.status = CertificateStatus.FAILED
                cert.error_message = str(e)
                failed_count += 1

            # Update progress per certificate
            job.successful_count = success_count
            job.failed_count = failed_count
            db.commit()

        # Final job status determination
        if failed_count == 0:
            job.status = JobStatus.COMPLETED
        elif success_count == 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.PARTIALLY_COMPLETED

        db.commit()
        logger.info(f"Job {job_id} finished with status {job.status} ({success_count} succeeded, {failed_count} failed)")

    except Exception as e:
        logger.exception(f"Unhandled exception in background job {job_id}: {e}")
        if job:
            job.status = JobStatus.FAILED
            db.commit()
    finally:
        db.close()
