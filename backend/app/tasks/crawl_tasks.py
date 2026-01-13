from celery import Celery
from app.config import get_settings
from app.database import SessionLocal
from app.models import Vendor, Document, DocumentChunk, CrawlJob, CrawlStatus
from app.services.crawler_simple import SimpleCrawler  # Using simple crawler
from app.services.embeddings import EmbeddingService
from datetime import datetime, timedelta
from uuid import UUID
import hashlib

settings = get_settings()

# Initialize Celery
celery_app = Celery(
    'vendorscope',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(name="crawl_vendor")
def crawl_vendor_task(vendor_id: str, job_id: str = None):
    """
    Celery task to crawl a vendor's trust pages
    
    Workflow:
    1. Initialize crawler
    2. Discover and crawl trust pages
    3. Detect document changes (versioning)
    4. Generate embeddings for new/updated documents
    5. Update vendor meta
    """
    db = SessionLocal()
    
    try:
        # Get vendor
        vendor = db.query(Vendor).filter(Vendor.id == UUID(vendor_id)).first()
        if not vendor:
            print(f"Vendor {vendor_id} not found")
            return
        
        # Create or get crawl job
        if job_id:
            crawl_job = db.query(CrawlJob).filter(CrawlJob.id == UUID(job_id)).first()
        else:
            crawl_job = CrawlJob(
                vendor_id=vendor.id,
                status=CrawlStatus.PENDING.value,
                job_type="full_crawl"
            )
            db.add(crawl_job)
            db.commit()
            db.refresh(crawl_job)
        
        # Update job status
        crawl_job.status = CrawlStatus.IN_PROGRESS.value
        crawl_job.started_at = datetime.utcnow()
        db.commit()
        
        print(f"Starting crawl for {vendor.name} ({vendor.domain})")
        
        # Initialize crawler (using SimpleCrawler for more permissive crawling)
        crawler = SimpleCrawler(
            domain=vendor.domain,
            seed_urls=vendor.seed_urls
        )
        
        # Crawl vendor
        crawl_results = crawler.crawl_vendor()
        crawler.close()
        
        print(f"Crawled {len(crawl_results)} pages for {vendor.name}")
        
        # Update vendor discovered URLs
        vendor.discovered_urls = [r['url'] for r in crawl_results]
        
        # Process each crawled page
        embedding_service = EmbeddingService()
        documents_created = 0
        documents_updated = 0
        
        for result in crawl_results:
            # Check if document exists
            existing_doc = db.query(Document).filter(
                Document.vendor_id == vendor.id,
                Document.url == result['url'],
                Document.is_latest == True
            ).first()
            
            if existing_doc:
                # Check if content changed
                if existing_doc.content_hash != result['content_hash']:
                    # Mark old version as not latest
                    existing_doc.is_latest = False
                    
                    # Create new version
                    new_doc = Document(
                        vendor_id=vendor.id,
                        url=result['url'],
                        url_hash=result['url_hash'],
                        document_type=result['document_type'].value,
                        title=result['title'],
                        raw_content=result['raw_content'],
                        cleaned_content=result['cleaned_content'],
                        content_hash=result['content_hash'],
                        version=existing_doc.version + 1,
                        is_latest=True,
                        previous_version_id=existing_doc.id,
                        crawled_at=datetime.utcnow(),
                        http_status=result['http_status'],
                        meta=result['meta']
                    )
                    db.add(new_doc)
                    db.flush()
                    
                    # Generate embeddings for new version
                    _create_embeddings(new_doc, embedding_service, db)
                    documents_updated += 1
                else:
                    # Content unchanged, just update crawl timestamp
                    existing_doc.crawled_at = datetime.utcnow()
            else:
                # New document
                new_doc = Document(
                    vendor_id=vendor.id,
                    url=result['url'],
                    url_hash=result['url_hash'],
                    document_type=result['document_type'].value,
                    title=result['title'],
                    raw_content=result['raw_content'],
                    cleaned_content=result['cleaned_content'],
                    content_hash=result['content_hash'],
                    version=1,
                    is_latest=True,
                    crawled_at=datetime.utcnow(),
                    http_status=result['http_status'],
                    meta=result['meta']
                )
                db.add(new_doc)
                db.flush()
                
                # Generate embeddings
                _create_embeddings(new_doc, embedding_service, db)
                documents_created += 1
        
        # Update vendor meta
        vendor.last_crawled_at = datetime.utcnow()
        
        # Schedule next crawl
        refresh_days = int(vendor.crawl_frequency_days)
        vendor.next_crawl_scheduled_at = datetime.utcnow() + timedelta(days=refresh_days)
        
        # Update crawl job
        crawl_job.status = CrawlStatus.COMPLETED.value
        crawl_job.completed_at = datetime.utcnow()
        crawl_job.pages_discovered = len(crawler.discovered_urls)
        crawl_job.pages_crawled = len(crawl_results)
        crawl_job.documents_created = documents_created
        crawl_job.documents_updated = documents_updated
        
        db.commit()
        
        print(f"Crawl completed for {vendor.name}: {documents_created} created, {documents_updated} updated")
        
        return {
            "vendor_id": vendor_id,
            "pages_crawled": len(crawl_results),
            "documents_created": documents_created,
            "documents_updated": documents_updated
        }
        
    except Exception as e:
        print(f"Error crawling vendor {vendor_id}: {str(e)}")
        
        if crawl_job:
            crawl_job.status = CrawlStatus.FAILED.value
            crawl_job.completed_at = datetime.utcnow()
            crawl_job.error_message = str(e)
            db.commit()
        
        raise
    
    finally:
        db.close()


def _create_embeddings(document: Document, embedding_service: EmbeddingService, db):
    """Helper to create embeddings for a document"""
    
    # Chunk and embed document
    embedded_chunks = embedding_service.embed_document(
        content=document.cleaned_content,
        meta={
            'url': document.url,
            'title': document.title,
            'document_type': document.document_type
        }
    )
    
    # Save chunks to database
    for chunk_data in embedded_chunks:
        chunk = DocumentChunk(
            document_id=document.id,
            vendor_id=document.vendor_id,
            chunk_text=chunk_data['text'],
            chunk_index=chunk_data['meta']['chunk_index'],
            embedding=chunk_data['embedding'],
            meta=chunk_data['meta']
        )
        db.add(chunk)
    
    db.flush()


def start_vendor_crawl(vendor_id: str):
    """Helper function to start a crawl task"""
    crawl_vendor_task.delay(vendor_id)


@celery_app.task(name="schedule_vendor_refreshes")
def schedule_vendor_refreshes():
    """
    Periodic task to schedule crawls for vendors that need refresh
    Run this every hour via Celery Beat
    """
    db = SessionLocal()
    
    try:
        # Find vendors that need refresh
        now = datetime.utcnow()
        vendors_to_refresh = db.query(Vendor).filter(
            Vendor.is_active == True,
            Vendor.next_crawl_scheduled_at <= now
        ).all()
        
        print(f"Scheduling refresh for {len(vendors_to_refresh)} vendors")
        
        for vendor in vendors_to_refresh:
            crawl_vendor_task.delay(str(vendor.id))
        
        return {
            "scheduled": len(vendors_to_refresh),
            "timestamp": now.isoformat()
        }
    
    finally:
        db.close()


# Celery Beat schedule
celery_app.conf.beat_schedule = {
    'schedule-vendor-refreshes': {
        'task': 'schedule_vendor_refreshes',
        'schedule': 3600.0,  # Every hour
    },
}