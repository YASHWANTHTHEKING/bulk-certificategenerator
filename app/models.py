import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"

class CertificateStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, index=True)
    event_name = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=False)
    issuer_name = Column(String(255), nullable=False)
    issuer_title = Column(String(255), nullable=True)
    custom_message = Column(Text, nullable=True)

    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    total_recipients = Column(Integer, default=0, nullable=False)
    successful_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    certificates = relationship("CertificateRecord", back_populates="job", cascade="all, delete-orphan")

class CertificateRecord(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, index=True)
    job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=False, index=True)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False, index=True)
    certificate_code = Column(String(64), unique=True, index=True, nullable=False)
    
    status = Column(Enum(CertificateStatus), default=CertificateStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=True)
    file_url = Column(String(512), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    job = relationship("GenerationJob", back_populates="certificates")
