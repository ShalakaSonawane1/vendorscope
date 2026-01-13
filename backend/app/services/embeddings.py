from openai import OpenAI
from typing import List, Dict
import tiktoken
from app.config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.OPENAI_API_KEY)


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
    
    def chunk_text(self, text: str, meta: Dict = None) -> List[Dict]:
        """
        Split text into overlapping chunks suitable for embedding
        
        Returns list of dicts with 'text' and 'meta'
        """
        # Tokenize
        tokens = self.encoding.encode(text)
        chunks = []
        
        # Create overlapping chunks
        start = 0
        chunk_index = 0
        
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # Skip very small chunks at the end
            if len(chunk_tokens) < 50:
                break
            
            chunk_meta = meta.copy() if meta else {}
            chunk_meta['chunk_index'] = chunk_index
            chunk_meta['start_token'] = start
            chunk_meta['end_token'] = end
            
            chunks.append({
                'text': chunk_text,
                'meta': chunk_meta
            })
            
            chunk_index += 1
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            response = client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch"""
        try:
            # OpenAI allows up to 2048 texts per batch
            batch_size = 2048
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)
            
            return all_embeddings
        except Exception as e:
            print(f"Error generating batch embeddings: {str(e)}")
            return []
    
    def embed_document(self, content: str, meta: Dict = None) -> List[Dict]:
        """
        Chunk and embed a document
        
        Returns list of dicts with 'text', 'embedding', and 'meta'
        """
        # Chunk the document
        chunks = self.chunk_text(content, meta)
        
        # Generate embeddings for all chunks
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.generate_embeddings_batch(texts)
        
        # Combine chunks with embeddings
        embedded_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            if embedding:  # Skip failed embeddings
                embedded_chunks.append({
                    'text': chunk['text'],
                    'embedding': embedding,
                    'meta': chunk['meta']
                })
        
        return embedded_chunks
    
    def similarity_search_query(self, query: str) -> List[float]:
        """Generate embedding for a search query"""
        return self.generate_embedding(query)