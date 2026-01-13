from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class QueryRequest(BaseModel):
    """Schema for querying about vendors"""
    query: str = Field(..., min_length=1, max_length=2000)
    vendor_ids: List[UUID] = Field(..., min_items=1)
    include_sources: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Is Stripe SOC 2 compliant?",
                "vendor_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "include_sources": True
            }
        }


class Citation(BaseModel):
    """A citation source"""
    document_id: UUID
    url: str
    title: Optional[str]
    excerpt: str
    relevance_score: float


class QueryResponse(BaseModel):
    """Schema for query response"""
    query: str
    answer: str
    risk_assessment: Optional[str] = None
    confidence_level: str = Field(..., description="low, medium, high")
    citations: List[Citation] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ComparisonRequest(BaseModel):
    """Schema for comparing multiple vendors"""
    vendor_ids: List[UUID] = Field(..., min_items=2, max_items=5)
    comparison_aspects: List[str] = Field(
        default_factory=lambda: ["security", "privacy", "compliance"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "vendor_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "550e8400-e29b-41d4-a716-446655440001"
                ],
                "comparison_aspects": ["security", "privacy", "compliance"]
            }
        }


class VendorComparison(BaseModel):
    """Comparison data for a single vendor"""
    vendor_id: UUID
    vendor_name: str
    security_score: Optional[str]
    privacy_score: Optional[str]
    compliance_status: Dict[str, bool]
    risk_level: str
    key_findings: List[str]
    citations: List[Citation]


class ComparisonResponse(BaseModel):
    """Schema for comparison response"""
    vendors: List[VendorComparison]
    summary: str
    recommendation: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)