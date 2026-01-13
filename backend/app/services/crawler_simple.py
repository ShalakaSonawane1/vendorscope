import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Set, Dict, Optional
import hashlib
import time
from app.config import get_settings
from app.models import DocumentType
import re

settings = get_settings()


class SimpleCrawler:
    """
    Simplified crawler that stores ALL relevant pages from known trust URLs
    More permissive - better for initial testing
    """
    
    def __init__(self, domain: str, seed_urls: List[str] = None):
        self.domain = domain.lower()
        self.seed_urls = seed_urls or []
        self.crawled_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()  # Add this line
        self.rate_limit = settings.CRAWLER_RATE_LIMIT_SECONDS
        
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": settings.CRAWLER_USER_AGENT}
        )
        
        # Pre-defined trust URLs to check
        self.trust_url_patterns = [
            f"https://{domain}/security",
            f"https://{domain}/trust",
            f"https://{domain}/privacy",
            f"https://{domain}/legal",
            f"https://{domain}/compliance",
            f"https://{domain}/terms",
            f"https://{domain}/policies",
            f"https://{domain}/docs/security",
            f"https://{domain}/about/security",
        ]
    
    def classify_document_type(self, url: str, soup: BeautifulSoup) -> DocumentType:
        """Classify document type based on URL and content"""
        url_lower = url.lower()
        text_sample = soup.get_text().lower()[:1000]
        
        if 'privacy' in url_lower or 'privacy policy' in text_sample:
            return DocumentType.PRIVACY_POLICY
        elif 'security' in url_lower:
            return DocumentType.SECURITY_PAGE
        elif 'trust' in url_lower:
            return DocumentType.TRUST_CENTER
        elif 'compliance' in url_lower or 'certifications' in url_lower:
            return DocumentType.COMPLIANCE_DOC
        elif 'terms' in url_lower:
            return DocumentType.TERMS_OF_SERVICE
        else:
            return DocumentType.OTHER
    
    def crawl_page(self, url: str) -> Optional[Dict]:
        """Crawl a single page and extract content"""
        if url in self.crawled_urls:
            return None
        
        try:
            # Rate limiting
            time.sleep(self.rate_limit)
            
            print(f"  📄 Fetching: {url}")
            response = self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else None
            
            # Clean content
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Generate hashes
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            content_hash = hashlib.sha256(text_content.encode()).hexdigest()
            
            self.crawled_urls.add(url)
            self.discovered_urls.add(url)  # Add this line
            
            print(f"  ✅ Success: {len(text_content)} chars, title: {title_text[:50] if title_text else 'N/A'}")
            
            return {
                'url': url,
                'url_hash': url_hash,
                'title': title_text,
                'raw_content': response.text,
                'cleaned_content': text_content,
                'content_hash': content_hash,
                'http_status': response.status_code,
                'document_type': self.classify_document_type(url, soup),
                'is_trust_page': True,  # All pages we crawl are considered trust pages
                'discovered_links': [],
                'meta': {  # Changed from 'metadata' to 'meta'
                    'content_type': response.headers.get('content-type'),
                    'last_modified': response.headers.get('last-modified'),
                }
            }
            
        except httpx.HTTPStatusError as e:
            print(f"  ❌ HTTP Error {e.response.status_code}: {url}")
            return None
        except Exception as e:
            print(f"  ❌ Error crawling {url}: {str(e)}")
            return None
    
    def crawl_vendor(self) -> List[Dict]:
        """
        Crawl vendor trust pages
        Uses predefined patterns + seed URLs + follows internal links
        """
        results = []
        
        # Combine seed URLs with common patterns
        urls_to_visit = set(self.seed_urls) if self.seed_urls else set()
        urls_to_visit.update(self.trust_url_patterns)
        
        print(f"\n🔍 Starting crawl for {self.domain}")
        print(f"   Starting with {len(urls_to_visit)} seed URLs")
        
        visited = set()
        
        while urls_to_visit and len(results) < 100:  # Limit to 100 successful pages
            if not urls_to_visit:
                break
                
            url = urls_to_visit.pop()
            
            if url in visited:
                continue
                
            visited.add(url)
            result = self.crawl_page(url)
            
            if result:
                results.append(result)
                
                # Extract and follow links from successful pages
                soup = BeautifulSoup(result['raw_content'], 'lxml')
                discovered_links = self.extract_links(url, soup)
                
                # Add new links to visit (filtering for trust-related pages)
                for link in discovered_links[:20]:  # Limit links per page
                    if link not in visited and len(results) < 100:
                        # Only follow links that look trust-related
                        if any(pattern in link.lower() for pattern in [
                            'security', 'privacy', 'legal', 'compliance', 
                            'trust', 'terms', 'policy', 'gdpr', 'certif'
                        ]):
                            urls_to_visit.add(link)
        
        print(f"\n✅ Crawl complete: {len(results)} pages retrieved")
        
        return results
    
    def extract_links(self, base_url: str, soup: BeautifulSoup) -> List[str]:
        """Extract and normalize links from page"""
        from urllib.parse import urljoin, urlparse
        
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            
            # Parse and normalize
            parsed = urlparse(full_url)
            
            # Must be same domain
            if not (parsed.netloc == f"www.{self.domain}" or 
                   parsed.netloc == self.domain or
                   parsed.netloc.endswith(f".{self.domain}")):
                continue
            
            # Remove fragments
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            
            # Skip non-relevant URLs
            skip_patterns = [
                '/cdn-cgi/', '/wp-admin/', '/cart', '/checkout',
                '/login', '/signup', '.jpg', '.png', '.pdf', '.zip'
            ]
            
            if any(pattern in normalized.lower() for pattern in skip_patterns):
                continue
                
            links.append(normalized)
        
        return list(set(links))
    
    def close(self):
        """Close HTTP client"""
        self.client.close()