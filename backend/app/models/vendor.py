from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.database import Base


class VendorType(str, enum.Enum):
    """Types of vendors"""
    PAYMENTS = "payments"
    CLOUD = "cloud"
    ANALYTICS = "analytics"
    SECURITY = "security"
    CUSTOMER_SUPPORT = "customer_support"
    MARKETING = "marketing"
    DATA_STORAGE = "data_storage"
    API_SERVICE = "api_service"
    OTHER = "other"


class RiskLevel(str, enum.Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class Vendor(Base):
    """Main vendor entity"""
    __tablename__ = "vendors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    vendor_type = Column(SQLEnum(VendorType), default=VendorType.OTHER)
    description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_critical = Column(Boolean, default=False)  # Critical vendors refresh more often
    
    # Discovery & crawling
    seed_urls = Column(JSONB, default=list)  # Initial URLs provided
    discovered_urls = Column(JSONB, default=list)  # Auto-discovered trust pages
    blocked_urls = Column(JSONB, default=list)  # URLs to skip
    
    # Crawl metadata
    last_crawled_at = Column(DateTime, nullable=True)
    next_crawl_scheduled_at = Column(DateTime, nullable=True)
    crawl_frequency_days = Column(String(50), default="30")  # or "7" for critical
    
    # Risk assessment (cached from latest analysis)
    current_risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.UNKNOWN)
    risk_summary = Column(Text, nullable=True)
    compliance_status = Column(JSONB, default=dict)  # {"SOC2": true, "GDPR": true}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="vendor", cascade="all, delete-orphan")
    crawl_jobs = relationship("CrawlJob", back_populates="vendor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vendor(name={self.name}, domain={self.domain})>"