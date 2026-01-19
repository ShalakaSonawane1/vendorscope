from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict
from uuid import UUID
from app.models import DocumentChunk, Document, Vendor
from app.services.embeddings import EmbeddingService
from app.config import get_settings

settings = get_settings()


class RAGEngine:
    """Retrieval-Augmented Generation engine for vendor documents"""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.top_k = settings.TOP_K_RESULTS
    
    def retrieve_relevant_chunks(
        self, 
        query: str, 
        vendor_ids: List[str],
        top_k: int = None,
        document_types: List[str] = None
    ) -> List[Dict]:
        """
        Retrieve most relevant document chunks for a query using vector similarity
        
        Returns list of dicts with chunk text, meta, and similarity score
        """
        if top_k is None:
            top_k = self.top_k
        
        # Generate query embedding
        query_embedding = self.embedding_service.similarity_search_query(query)
        if not query_embedding:
            return []
        
        # Convert embedding to PostgreSQL vector format
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # Build query with filters
        query_sql = """
            SELECT 
                dc.id,
                dc.chunk_text,
                dc.meta,
                d.url,
                d.title,
                d.document_type,
                v.name as vendor_name,
                v.id as vendor_id,
                1 - (dc.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            JOIN vendors v ON dc.vendor_id = v.id
            WHERE dc.vendor_id IN :vendor_ids
            AND d.is_latest = true
        """
        
        params = {
            'embedding': embedding_str,
            'vendor_ids': tuple([UUID(vid) for vid in vendor_ids])
        }
        
        # Add document type filter if specified
        if document_types:
            query_sql += " AND d.document_type IN :doc_types"
            params['doc_types'] = tuple(document_types)
        
        query_sql += """
            ORDER BY dc.embedding <=> :embedding::vector
            LIMIT :limit
        """
        params['limit'] = top_k
        
        # Execute query
        result = self.db.execute(text(query_sql), params)
        rows = result.fetchall()
        
        # Format results
        chunks = []
        for row in rows:
            chunks.append({
                'chunk_id': str(row.id),
                'text': row.chunk_text,
                'meta': row.meta,
                'url': row.url,
                'title': row.title,
                'document_type': row.document_type,
                'vendor_name': row.vendor_name,
                'vendor_id': str(row.vendor_id),
                'similarity': float(row.similarity)
            })
        
        return chunks
    
    def retrieve_vendor_context(self, vendor_id: str) -> Dict:
        """Get high-level vendor information for context"""
        vendor = self.db.query(Vendor).filter(Vendor.id == UUID(vendor_id)).first()
        if not vendor:
            return {}
        
        return {
            'name': vendor.name,
            'domain': vendor.domain,
            'type': vendor.vendor_type.value,
            'risk_level': vendor.current_risk_level.value,
            'compliance_status': vendor.compliance_status,
            'last_crawled': vendor.last_crawled_at.isoformat() if vendor.last_crawled_at else None
        }
    
    def get_document_by_url(self, url: str, vendor_id: str = None) -> Dict:
        """Retrieve a specific document by URL"""
        query = self.db.query(Document).filter(
            Document.url == url,
            Document.is_latest == True
        )
        
        if vendor_id:
            query = query.filter(Document.vendor_id == UUID(vendor_id))
        
        doc = query.first()
        if not doc:
            return None
        
        return {
            'id': str(doc.id),
            'url': doc.url,
            'title': doc.title,
            'content': doc.cleaned_content,
            'type': doc.document_type,
            'crawled_at': doc.crawled_at.isoformat()
        }
    
    def build_context_for_llm(
        self, 
        query: str, 
        vendor_ids: List[str],
        document_types: List[str] = None
    ) -> str:
        """
        Build formatted context string for LLM from retrieved chunks
        """
        chunks = self.retrieve_relevant_chunks(
            query=query,
            vendor_ids=vendor_ids,
            document_types=document_types
        )
        
        if not chunks:
            return "No relevant information found in vendor documents."
        
        # Format context
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}]\n"
                f"Vendor: {chunk['vendor_name']}\n"
                f"Document: {chunk['title'] or 'Untitled'}\n"
                f"URL: {chunk['url']}\n"
                f"Type: {chunk['document_type']}\n"
                f"Content:\n{chunk['text']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def get_citations(
        self,
        query: str,
        vendor_ids: List[str],
        top_k: int = 3
    ) -> List[Dict]:
        """Get citations for a query response"""
        chunks = self.retrieve_relevant_chunks(
            query=query,
            vendor_ids=vendor_ids,
            top_k=top_k
        )
        
        # Deduplicate by document
        seen_docs = set()
        citations = []
        
        for chunk in chunks:
            doc_key = (chunk['vendor_id'], chunk['url'])
            if doc_key not in seen_docs:
                seen_docs.add(doc_key)
                citations.append({
                    'url': chunk['url'],
                    'title': chunk['title'],
                    'excerpt': chunk['text'][:200] + "...",
                    'relevance_score': chunk['similarity']
                })
        
        return citations