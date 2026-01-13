from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Vendor
from app.schemas.query import (
    QueryRequest, QueryResponse, 
    ComparisonRequest, ComparisonResponse
)
from app.services.agent import VendorAnalysisAgent
import time

router = APIRouter()


@router.post("/ask", response_model=QueryResponse)
async def ask_query(
    query_request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about one or more vendors.
    
    Example queries:
    - "Is Stripe SOC 2 compliant?"
    - "What security incidents has Cloudflare had?"
    - "Does Zendesk share data with third parties?"
    """
    
    start_time = time.time()
    
    # Validate vendors exist
    vendors = db.query(Vendor).filter(
        Vendor.id.in_(query_request.vendor_ids)
    ).all()
    
    if len(vendors) != len(query_request.vendor_ids):
        raise HTTPException(
            status_code=404, 
            detail="One or more vendors not found"
        )
    
    # Check if vendors have been crawled
    uncrawled = [v.name for v in vendors if v.last_crawled_at is None]
    if uncrawled:
        raise HTTPException(
            status_code=400,
            detail=f"The following vendors haven't been crawled yet: {', '.join(uncrawled)}. Please wait for initial crawl to complete."
        )
    
    # Initialize agent and process query
    agent = VendorAnalysisAgent(db)
    result = await agent.process_query(
        query=query_request.query,
        vendor_ids=[str(v.id) for v in vendors],
        include_sources=query_request.include_sources
    )
    
    processing_time = int((time.time() - start_time) * 1000)
    
    return QueryResponse(
        query=query_request.query,
        answer=result["answer"],
        risk_assessment=result.get("risk_assessment"),
        confidence_level=result["confidence_level"],
        citations=result.get("citations", []),
        metadata=result.get("metadata", {}),
        processing_time_ms=processing_time
    )


@router.post("/compare", response_model=ComparisonResponse)
async def compare_vendors(
    comparison_request: ComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare multiple vendors across security, privacy, and compliance.
    
    Supports 2-5 vendors at a time.
    """
    
    # Validate vendors exist
    vendors = db.query(Vendor).filter(
        Vendor.id.in_(comparison_request.vendor_ids)
    ).all()
    
    if len(vendors) != len(comparison_request.vendor_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more vendors not found"
        )
    
    # Check if vendors have been crawled
    uncrawled = [v.name for v in vendors if v.last_crawled_at is None]
    if uncrawled:
        raise HTTPException(
            status_code=400,
            detail=f"The following vendors haven't been crawled yet: {', '.join(uncrawled)}"
        )
    
    # Initialize agent and process comparison
    agent = VendorAnalysisAgent(db)
    result = await agent.compare_vendors(
        vendor_ids=[str(v.id) for v in vendors],
        aspects=comparison_request.comparison_aspects
    )
    
    return result