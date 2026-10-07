import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models import JobStatus, CertificateStatus

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class RecipientInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Full name of recipient")
    email: str = Field(..., description="Valid email address of recipient")
    custom_identifier: Optional[str] = Field(None, max_length=100, description="Optional custom ID/Roll No")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Recipient name cannot be empty or whitespace only.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip()
        if not re.match(EMAIL_REGEX, cleaned):
            raise ValueError(f"Invalid email address format: '{cleaned}'")
        return cleaned.lower()

class CertificateJobCreateRequest(BaseModel):
    event_name: str = Field(..., min_length=2, max_length=200, description="Name of the course or event")
    issue_date: Optional[str] = Field(None, description="Issue date in YYYY-MM-DD or readable format (default: today)")
    issuer_name: str = Field(..., min_length=1, max_length=150, description="Name of issuing authority / organization")
    issuer_title: Optional[str] = Field(None, max_length=100, description="Title of the issuer (e.g. Director, Lead Instructor)")
    custom_message: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Optional achievement text, e.g., 'for successfully completing the Advanced Python program with distinction.'"
    )
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipient details")

    @field_validator("event_name", "issuer_name")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or blank spaces.")
        return cleaned

class CertificateItemResponse(BaseModel):
    id: str
    recipient_name: str
    recipient_email: str
    certificate_code: str
    status: CertificateStatus
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobStatusResponse(BaseModel):
    job_id: str
    event_name: str
    issuer_name: str
    status: JobStatus
    total_recipients: int
    successful_count: int
    failed_count: int
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    certificates: Optional[List[CertificateItemResponse]] = None

    model_config = ConfigDict(from_attributes=True)

class JobCreationResponse(BaseModel):
    job_id: str
    status: JobStatus
    total_recipients: int
    message: str
