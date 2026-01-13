from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class CrawlStatus(str, enum.Enum):
    """Status of crawl jobs"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlJob(Base):
    """Tracks crawling jobs for vendors"""
    __tablename__ = "crawl_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    
    # Job details
    status = Column(String(50), default=CrawlStatus.PENDING.value, index=True)
    job_type = Column(String(50), default="full_crawl")  # full_crawl, incremental, targeted
    
    # Execution tracking
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    celery_task_id = Column(String(255), nullable=True, index=True)
    
    # Results
    pages_discovered = Column(Integer, default=0)
    pages_crawled = Column(Integer, default=0)
    pages_failed = Column(Integer, default=0)
    documents_created = Column(Integer, default=0)
    documents_updated = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, default=dict)
    
    # Configuration used
    config = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="crawl_jobs")
    
    def __repr__(self):
        return f"<CrawlJob(vendor_id={self.vendor_id}, status={self.status})>"