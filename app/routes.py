import os
import io
import zipfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import GenerationJob, CertificateRecord, JobStatus, CertificateStatus
from app.schemas import (
    CertificateJobCreateRequest,
    JobCreationResponse,
    JobStatusResponse,
    CertificateItemResponse
)
from app.services import create_job, process_job_batch

router = APIRouter(prefix="/api", tags=["Certificates"])

@router.post(
    "/certificates/generate",
    response_model=JobCreationResponse,
    status_code=202,
    summary="Submit bulk certificate generation request"
)
def submit_generation_job(
    request: CertificateJobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submits a batch of recipients for certificate generation.
    Validates payload and starts generation asynchronously in the background.
    Returns 202 Accepted with job ID for status tracking.
    """
    job = create_job(db=db, request_data=request)
    
    # Offload processing to background task
    background_tasks.add_task(process_job_batch, job.id, SessionLocal)

    return JobCreationResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_recipients,
        message="Certificate generation job accepted and processing in the background."
    )

@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status and progress"
)
def get_job_status(
    job_id: str,
    include_certificates: bool = Query(True, description="Whether to include recipient certificate items"),
    db: Session = Depends(get_db)
):
    """
    Retrieves the status, completion metrics, and individual certificate statuses of a job.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found.")

    processed = job.successful_count + job.failed_count
    progress = round((processed / job.total_recipients * 100), 2) if job.total_recipients > 0 else 0.0

    cert_items = []
    if include_certificates:
        for cert in job.certificates:
            cert_items.append(
                CertificateItemResponse(
                    id=cert.id,
                    recipient_name=cert.recipient_name,
                    recipient_email=cert.recipient_email,
                    certificate_code=cert.certificate_code,
                    status=cert.status,
                    error_message=cert.error_message,
                    download_url=cert.file_url if cert.status == CertificateStatus.SUCCESS else None,
                    created_at=cert.created_at,
                    updated_at=cert.updated_at
                )
            )

    return JobStatusResponse(
        job_id=job.id,
        event_name=job.event_name,
        issuer_name=job.issuer_name,
        status=job.status,
        total_recipients=job.total_recipients,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        progress_percentage=progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
        certificates=cert_items if include_certificates else None
    )

@router.get(
    "/jobs",
    response_model=List[JobStatusResponse],
    summary="List all certificate generation jobs"
)
def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Lists generation jobs with pagination.
    """
    jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).offset(offset).limit(limit).all()
    results = []
    for job in jobs:
        processed = job.successful_count + job.failed_count
        progress = round((processed / job.total_recipients * 100), 2) if job.total_recipients > 0 else 0.0
        results.append(
            JobStatusResponse(
                job_id=job.id,
                event_name=job.event_name,
                issuer_name=job.issuer_name,
                status=job.status,
                total_recipients=job.total_recipients,
                successful_count=job.successful_count,
                failed_count=job.failed_count,
                progress_percentage=progress,
                created_at=job.created_at,
                updated_at=job.updated_at,
                certificates=None
            )
        )
    return results

@router.get(
    "/certificates/{cert_id}/download",
    summary="Download single generated certificate PDF"
)
def download_certificate(cert_id: str, db: Session = Depends(get_db)):
    """
    Download a single generated certificate PDF by certificate ID.
    """
    cert = db.query(CertificateRecord).filter(CertificateRecord.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found.")

    if cert.status != CertificateStatus.SUCCESS or not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(
            status_code=400,
            detail=f"Certificate file is not available. Status: {cert.status}. Error: {cert.error_message}"
        )

    filename = os.path.basename(cert.file_path)
    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        filename=filename
    )

@router.get(
    "/jobs/{job_id}/download-zip",
    summary="Download all successfully generated certificates in a ZIP archive"
)
def download_job_certificates_zip(job_id: str, db: Session = Depends(get_db)):
    """
    Bundles all successfully generated certificates for a job into a downloadable ZIP archive.
    """
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found.")

    successful_certs = [
        c for c in job.certificates
        if c.status == CertificateStatus.SUCCESS and c.file_path and os.path.exists(c.file_path)
    ]

    if not successful_certs:
        raise HTTPException(
            status_code=400,
            detail="No generated certificates available to download for this job yet."
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for cert in successful_certs:
            arcname = os.path.basename(cert.file_path)
            zf.write(cert.file_path, arcname=arcname)

    zip_buffer.seek(0)
    safe_event_name = "".join(c for c in job.event_name if c.isalnum() or c in "._-").strip() or "certificates"
    download_filename = f"{safe_event_name}_{job_id[:8]}_certificates.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{download_filename}"'}
    )
