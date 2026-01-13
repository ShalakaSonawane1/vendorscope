from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid
import enum
from app.database import Base
from app.config import get_settings

settings = get_settings()


class DocumentType(str, enum.Enum):
    """Types of documents we track"""
    SECURITY_PAGE = "security_page"
    PRIVACY_POLICY = "privacy_policy"
    TRUST_CENTER = "trust_center"
    COMPLIANCE_DOC = "compliance_doc"
    STATUS_PAGE = "status_page"
    BLOG_POST = "blog_post"
    INCIDENT_REPORT = "incident_report"
    TERMS_OF_SERVICE = "terms_of_service"
    OTHER = "other"


class Document(Base):
    """Versioned documents from vendor sources"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    
    # Document identity
    url = Column(String(2048), nullable=False, index=True)
    url_hash = Column(String(64), nullable=False, index=True)  # SHA-256 for deduplication
    document_type = Column(String(50), default=DocumentType.OTHER.value)
    title = Column(String(500), nullable=True)
    
    # Content
    raw_content = Column(Text, nullable=False)  # Full HTML/text
    cleaned_content = Column(Text, nullable=False)  # Processed text for RAG
    content_hash = Column(String(64), nullable=False)  # Detect changes
    
    # Versioning
    version = Column(Integer, default=1)
    is_latest = Column(Boolean, default=True, index=True)
    previous_version_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    
    # meta
    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    http_status = Column(Integer, nullable=True)
    meta = Column(JSONB, default=dict)  # Extra info: headers, last-modified, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    previous_version = relationship("Document", remote_side=[id], backref="next_versions")
    
    # Indexes
    __table_args__ = (
        Index('idx_vendor_url_latest', 'vendor_id', 'url', 'is_latest'),
        Index('idx_vendor_type', 'vendor_id', 'document_type'),
    )
    
    def __repr__(self):
        return f"<Document(url={self.url}, version={self.version})>"


class DocumentChunk(Base):
    """Chunked documents with embeddings for RAG"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    
    # Chunk content
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Position in document
    
    # Vector embedding
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=False)
    
    # meta for context
    meta = Column(JSONB, default=dict)  # {"section": "Security", "url": "..."}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    # Indexes for vector search
    __table_args__ = (
        Index('idx_vendor_chunks', 'vendor_id'),
        Index(
            'idx_embedding_cosine',
            'embedding',
            postgresql_using='ivfflat',
            postgresql_with={'lists': 100},
            postgresql_ops={'embedding': 'vector_cosine_ops'}
        ),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(document_id={self.document_id}, index={self.chunk_index})>"