from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.models import Vendor, Document
from app.schemas.vendor import (
    VendorCreate, VendorUpdate, VendorResponse, 
    VendorDetail, VendorList
)
from app.tasks.crawl_tasks import start_vendor_crawl
import math

router = APIRouter()


@router.post("/", response_model=VendorResponse, status_code=201)
async def create_vendor(
    vendor: VendorCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new vendor and start initial crawl"""
    
    # Check if vendor already exists
    existing = db.query(Vendor).filter(Vendor.domain == vendor.domain).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Vendor with domain '{vendor.domain}' already exists")
    
    # Create vendor
    db_vendor = Vendor(
        name=vendor.name,
        domain=vendor.domain,
        vendor_type=vendor.vendor_type,
        description=vendor.description,
        seed_urls=vendor.seed_urls,
        is_critical=vendor.is_critical,
        crawl_frequency_days="7" if vendor.is_critical else "30",
    )
    
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
    # Start initial crawl in background
    background_tasks.add_task(start_vendor_crawl, str(db_vendor.id))
    
    # Prepare response
    response = VendorResponse.model_validate(db_vendor)
    response.total_documents = 0
    response.discovered_urls_count = len(db_vendor.discovered_urls)
    
    return response


@router.get("/", response_model=VendorList)
async def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    vendor_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all vendors with filtering and pagination"""
    
    query = db.query(Vendor)
    
    # Apply filters
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Vendor.name.ilike(search_filter)) | 
            (Vendor.domain.ilike(search_filter))
        )
    
    if vendor_type:
        query = query.filter(Vendor.vendor_type == vendor_type)
    
    if risk_level:
        query = query.filter(Vendor.current_risk_level == risk_level)
    
    if is_active is not None:
        query = query.filter(Vendor.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    vendors = query.order_by(Vendor.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Enrich with document counts
    vendor_responses = []
    for vendor in vendors:
        doc_count = db.query(func.count(Document.id)).filter(
            Document.vendor_id == vendor.id,
            Document.is_latest == True
        ).scalar()
        
        response = VendorResponse.model_validate(vendor)
        response.total_documents = doc_count
        response.discovered_urls_count = len(vendor.discovered_urls)
        vendor_responses.append(response)
    
    return VendorList(
        vendors=vendor_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size)
    )


@router.get("/{vendor_id}", response_model=VendorDetail)
async def get_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    """Get vendor details by ID"""
    
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    doc_count = db.query(func.count(Document.id)).filter(
        Document.vendor_id == vendor.id,
        Document.is_latest == True
    ).scalar()
    
    response = VendorDetail.model_validate(vendor)
    response.total_documents = doc_count
    response.discovered_urls_count = len(vendor.discovered_urls)
    
    return response


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: UUID,
    vendor_update: VendorUpdate,
    db: Session = Depends(get_db)
):
    """Update vendor information"""
    
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Update fields
    update_data = vendor_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)
    
    db.commit()
    db.refresh(vendor)
    
    doc_count = db.query(func.count(Document.id)).filter(
        Document.vendor_id == vendor.id,
        Document.is_latest == True
    ).scalar()
    
    response = VendorResponse.model_validate(vendor)
    response.total_documents = doc_count
    response.discovered_urls_count = len(vendor.discovered_urls)
    
    return response


@router.delete("/{vendor_id}", status_code=204)
async def delete_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    """Delete a vendor and all associated data"""
    
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    db.delete(vendor)
    db.commit()
    
    return None


@router.post("/{vendor_id}/crawl", status_code=202)
async def trigger_crawl(
    vendor_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually trigger a crawl for a vendor"""
    
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    background_tasks.add_task(start_vendor_crawl, str(vendor_id))
    
    return {"message": "Crawl job started", "vendor_id": vendor_id}