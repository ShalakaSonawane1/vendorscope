import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Set, Dict, Optional
import hashlib
import time
from app.config import get_settings
from app.models import Document, DocumentType
import re

settings = get_settings()


class SmartCrawler:
    """
    Intelligent crawler that discovers vendor trust pages automatically
    """
    
    def __init__(self, domain: str, seed_urls: List[str] = None):
        self.domain = domain.lower()
        self.seed_urls = seed_urls or []
        self.discovered_urls: Set[str] = set()
        self.crawled_urls: Set[str] = set()
        self.max_pages = settings.CRAWLER_MAX_PAGES_PER_VENDOR
        self.rate_limit = settings.CRAWLER_RATE_LIMIT_SECONDS
        
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": settings.CRAWLER_USER_AGENT}
        )
    
    def is_allowed_url(self, url: str) -> bool:
        """Check if URL is allowed to crawl"""
        parsed = urlparse(url)
        
        # Must be same domain or subdomain
        if not (parsed.netloc == self.domain or parsed.netloc.endswith(f".{self.domain}")):
            return False
        
        # Skip common non-content URLs
        skip_patterns = [
            r'/cdn-cgi/',
            r'/wp-admin/',
            r'/wp-content/',
            r'/cart',
            r'/checkout',
            r'/login',
            r'/signup',
            r'/register',
            r'\.(jpg|jpeg|png|gif|pdf|zip|exe)$',
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True
    
    def is_trust_page(self, url: str, soup: BeautifulSoup) -> bool:
        """
        Determine if a page is a trust/security/compliance page
        Uses URL patterns and content analysis
        """
        url_lower = url.lower()
        
        # Check URL patterns - if URL matches, it's definitely a trust page
        for pattern in settings.TRUST_PAGE_PATTERNS:
            if pattern in url_lower:
                return True
        
        # Check page content for trust indicators (relaxed threshold)
        text = soup.get_text().lower()
        trust_keywords = [
            'security', 'privacy', 'compliance', 'soc 2', 'soc2', 'iso 27001',
            'gdpr', 'hipaa', 'trust center', 'certifications', 'certificate',
            'data protection', 'incident', 'vulnerability', 'encryption',
            'authentication', 'authorization', 'pci', 'terms', 'policy'
        ]
        
        keyword_count = sum(1 for kw in trust_keywords if kw in text)
        # Reduced from 3 to 2 - more lenient
        return keyword_count >= 2
    
    def classify_document_type(self, url: str, soup: BeautifulSoup) -> DocumentType:
        """Classify document type based on URL and content"""
        url_lower = url.lower()
        
        if 'privacy' in url_lower or 'privacy policy' in soup.get_text().lower()[:500]:
            return DocumentType.PRIVACY_POLICY
        elif 'security' in url_lower:
            return DocumentType.SECURITY_PAGE
        elif 'trust' in url_lower:
            return DocumentType.TRUST_CENTER
        elif 'compliance' in url_lower or 'certifications' in url_lower:
            return DocumentType.COMPLIANCE_DOC
        elif 'status' in url_lower or 'uptime' in url_lower:
            return DocumentType.STATUS_PAGE
        elif 'blog' in url_lower or 'incident' in url_lower:
            return DocumentType.BLOG_POST
        elif 'terms' in url_lower:
            return DocumentType.TERMS_OF_SERVICE
        else:
            return DocumentType.OTHER
    
    def extract_links(self, base_url: str, soup: BeautifulSoup) -> List[str]:
        """Extract and normalize links from page"""
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            
            # Remove fragments and normalize
            parsed = urlparse(full_url)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            if parsed.query:
                normalized += f"?{parsed.query}"
            
            if self.is_allowed_url(normalized):
                links.append(normalized)
        
        return list(set(links))
    
    def crawl_page(self, url: str) -> Optional[Dict]:
        """Crawl a single page and extract content"""
        if url in self.crawled_urls:
            return None
        
        try:
            # Rate limiting
            time.sleep(self.rate_limit)
            
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
            
            # Extract links for discovery
            links = self.extract_links(url, soup)
            
            self.crawled_urls.add(url)
            
            return {
                'url': url,
                'url_hash': url_hash,
                'title': title_text,
                'raw_content': response.text,
                'cleaned_content': text_content,
                'content_hash': content_hash,
                'http_status': response.status_code,
                'document_type': self.classify_document_type(url, soup),
                'is_trust_page': self.is_trust_page(url, soup),
                'discovered_links': links,
                'metadata': {
                    'content_type': response.headers.get('content-type'),
                    'last_modified': response.headers.get('last-modified'),
                }
            }
            
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            return None
    
    def discover_trust_pages(self) -> List[str]:
        """
        Discover trust pages starting from seed URLs or domain root
        """
        # Start with seed URLs or domain root
        if self.seed_urls:
            to_visit = set(self.seed_urls)
        else:
            to_visit = {
                f"https://{self.domain}",
                f"https://{self.domain}/security",
                f"https://{self.domain}/trust",
                f"https://{self.domain}/privacy",
                f"https://{self.domain}/legal",
            }
        
        trust_pages = []
        
        while to_visit and len(self.crawled_urls) < self.max_pages:
            url = to_visit.pop()
            
            if url in self.crawled_urls:
                continue
            
            result = self.crawl_page(url)
            if not result:
                continue
            
            # If it's a trust page, add to results
            if result['is_trust_page']:
                trust_pages.append(url)
                self.discovered_urls.add(url)
                
                # Add discovered links to explore
                for link in result['discovered_links']:
                    if link not in self.crawled_urls:
                        to_visit.add(link)
        
        return trust_pages
    
    def crawl_vendor(self) -> List[Dict]:
        """
        Main crawl method - discovers and crawls trust pages
        Returns list of crawled page data
        """
        # First, discover trust pages
        trust_pages = self.discover_trust_pages()
        
        # Now crawl all discovered trust pages
        results = []
        for url in trust_pages:
            result = self.crawl_page(url)
            if result:
                results.append(result)
        
        return results
    
    def close(self):
        """Close HTTP client"""
        self.client.close()