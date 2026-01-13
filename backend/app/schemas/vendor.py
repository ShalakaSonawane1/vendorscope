from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from app.models.vendor import VendorType, RiskLevel


class VendorCreate(BaseModel):
    """Schema for creating a new vendor"""
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    vendor_type: VendorType = VendorType.OTHER
    description: Optional[str] = None
    seed_urls: List[str] = Field(default_factory=list)
    is_critical: bool = False
    
    @validator('domain')
    def validate_domain(cls, v):
        """Ensure domain doesn't include protocol"""
        v = v.lower().strip()
        if v.startswith(('http://', 'https://')):
            raise ValueError("Domain should not include protocol (http:// or https://)")
        if v.startswith('www.'):
            v = v[4:]
        return v
    
    @validator('seed_urls')
    def validate_seed_urls(cls, v, values):
        """Validate seed URLs belong to the domain"""
        if 'domain' not in values:
            return v
        domain = values['domain']
        validated = []
        for url in v:
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
            if domain in url:
                validated.append(url)
        return validated


class VendorUpdate(BaseModel):
    """Schema for updating vendor"""
    name: Optional[str] = None
    description: Optional[str] = None
    vendor_type: Optional[VendorType] = None
    is_critical: Optional[bool] = None
    is_active: Optional[bool] = None
    seed_urls: Optional[List[str]] = None


class VendorResponse(BaseModel):
    """Schema for vendor response"""
    id: UUID
    name: str
    domain: str
    vendor_type: VendorType
    description: Optional[str]
    is_active: bool
    is_critical: bool
    current_risk_level: RiskLevel
    risk_summary: Optional[str]
    compliance_status: Dict
    last_crawled_at: Optional[datetime]
    next_crawl_scheduled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Counts
    total_documents: int = 0
    discovered_urls_count: int = 0
    
    class Config:
        from_attributes = True


class VendorDetail(VendorResponse):
    """Extended vendor response with more details"""
    seed_urls: List[str]
    discovered_urls: List[str]
    
    class Config:
        from_attributes = True


class VendorList(BaseModel):
    """Paginated vendor list"""
    vendors: List[VendorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int