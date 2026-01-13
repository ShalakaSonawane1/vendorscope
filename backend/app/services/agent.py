from openai import OpenAI
from sqlalchemy.orm import Session
from typing import List, Dict
from app.services.rag_engine import RAGEngine
from app.models import Vendor
from app.schemas.query import Citation, VendorComparison, ComparisonResponse
from uuid import UUID
from app.config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.OPENAI_API_KEY)


class VendorAnalysisAgent:
    """
    AI Agent for vendor risk analysis and due diligence
    
    Capabilities:
    - Answer questions about vendors with citations
    - Assess risk levels
    - Compare multiple vendors
    - Detect changes in vendor posture
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.rag_engine = RAGEngine(db)
        self.model = settings.OPENAI_CHAT_MODEL
    
    async def process_query(
        self,
        query: str,
        vendor_ids: List[str],
        include_sources: bool = True
    ) -> Dict:
        """
        Process a user query about vendors
        
        Agent workflow:
        1. Retrieve relevant context
        2. Analyze query intent
        3. Generate grounded response
        4. Extract risk assessment
        5. Provide citations
        """
        
        # Step 1: Build context from RAG
        context = self.rag_engine.build_context_for_llm(query, vendor_ids)
        
        # Get vendor info for additional context
        vendor_contexts = [
            self.rag_engine.retrieve_vendor_context(vid) 
            for vid in vendor_ids
        ]
        
        # Step 2: Build prompt for LLM
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_query_prompt(query, context, vendor_contexts)
        
        # Step 3: Get LLM response
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for factual responses
            max_tokens=1500
        )
        
        answer_text = response.choices[0].message.content
        
        # Step 4: Parse response
        parsed = self._parse_agent_response(answer_text)
        
        # Step 5: Get citations if requested
        citations = []
        if include_sources:
            citation_data = self.rag_engine.get_citations(query, vendor_ids, top_k=5)
            citations = [
                Citation(
                    document_id=UUID(vendor_ids[0]),  # Simplified
                    url=c['url'],
                    title=c['title'],
                    excerpt=c['excerpt'],
                    relevance_score=c['relevance_score']
                )
                for c in citation_data
            ]
        
        return {
            "answer": parsed['answer'],
            "risk_assessment": parsed.get('risk_assessment'),
            "confidence_level": parsed['confidence_level'],
            "citations": citations,
            "metadata": {
                "sources_used": len(context.split("---")),
                "vendors_analyzed": len(vendor_ids)
            }
        }
    
    async def compare_vendors(
        self,
        vendor_ids: List[str],
        aspects: List[str]
    ) -> ComparisonResponse:
        """
        Compare multiple vendors across specified aspects
        """
        
        vendor_comparisons = []
        
        for vendor_id in vendor_ids:
            vendor = self.db.query(Vendor).filter(Vendor.id == UUID(vendor_id)).first()
            if not vendor:
                continue
            
            # Build comparison query
            comparison_query = f"Analyze {vendor.name} for: {', '.join(aspects)}"
            
            # Get vendor-specific analysis
            result = await self.process_query(
                query=comparison_query,
                vendor_ids=[vendor_id],
                include_sources=True
            )
            
            # Extract structured data
            comparison = VendorComparison(
                vendor_id=UUID(vendor_id),
                vendor_name=vendor.name,
                security_score=self._extract_score(result['answer'], 'security'),
                privacy_score=self._extract_score(result['answer'], 'privacy'),
                compliance_status=vendor.compliance_status,
                risk_level=vendor.current_risk_level.value,
                key_findings=self._extract_key_findings(result['answer']),
                citations=result['citations']
            )
            
            vendor_comparisons.append(comparison)
        
        # Generate overall summary
        summary = await self._generate_comparison_summary(vendor_comparisons, aspects)
        
        return ComparisonResponse(
            vendors=vendor_comparisons,
            summary=summary['summary'],
            recommendation=summary.get('recommendation')
        )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for the agent"""
        return """You are VendorScope, an AI agent specialized in vendor risk assessment and security due diligence.

Your capabilities:
- Analyze vendor security postures
- Assess compliance status (SOC 2, GDPR, HIPAA, etc.)
- Identify security incidents and vulnerabilities
- Evaluate privacy practices
- Provide evidence-based risk assessments

Critical instructions:
1. Base ALL answers on the provided context documents
2. NEVER speculate or make claims without evidence
3. If information is not in the context, clearly state "This information is not available in the vendor's public documentation"
4. Cite specific document sections when making claims
5. Assess confidence level: HIGH (multiple sources), MEDIUM (single source), LOW (unclear/conflicting)
6. For risk assessments, use: LOW, MEDIUM, HIGH, or UNKNOWN

Response structure:
- Direct answer to the question
- Supporting evidence with specifics
- Risk assessment (if applicable)
- Confidence level
- Note any uncertainties or gaps

Be precise, factual, and helpful."""
    
    def _build_query_prompt(
        self,
        query: str,
        context: str,
        vendor_contexts: List[Dict]
    ) -> str:
        """Build user prompt with query and context"""
        
        vendor_info = "\n".join([
            f"- {v['name']} ({v['domain']}): {v['type']}"
            for v in vendor_contexts
        ])
        
        return f"""User question: {query}

Vendors being analyzed:
{vendor_info}

Retrieved documents and information:
{context}

Please provide a comprehensive, evidence-based answer. Include:
1. Direct answer to the question
2. Specific evidence from documents (quote key phrases)
3. Risk assessment if relevant
4. Confidence level (HIGH/MEDIUM/LOW)
5. Any important caveats or missing information

Format your response clearly and cite sources."""
    
    def _parse_agent_response(self, response_text: str) -> Dict:
        """Parse LLM response into structured data"""
        
        # Simple parsing - in production, use structured output
        lines = response_text.strip().split('\n')
        
        confidence = "medium"
        risk = None
        
        # Extract confidence level
        for line in lines:
            lower_line = line.lower()
            if 'confidence' in lower_line:
                if 'high' in lower_line:
                    confidence = "high"
                elif 'low' in lower_line:
                    confidence = "low"
            
            if 'risk' in lower_line:
                if 'low risk' in lower_line:
                    risk = "low"
                elif 'medium risk' in lower_line or 'moderate risk' in lower_line:
                    risk = "medium"
                elif 'high risk' in lower_line:
                    risk = "high"
        
        return {
            "answer": response_text,
            "confidence_level": confidence,
            "risk_assessment": risk
        }
    
    def _extract_score(self, text: str, aspect: str) -> str:
        """Extract score for a specific aspect (simplified)"""
        text_lower = text.lower()
        if aspect.lower() in text_lower:
            if 'strong' in text_lower or 'good' in text_lower:
                return "Good"
            elif 'adequate' in text_lower or 'acceptable' in text_lower:
                return "Adequate"
            elif 'weak' in text_lower or 'poor' in text_lower:
                return "Needs Improvement"
        return "Not Assessed"
    
    def _extract_key_findings(self, text: str) -> List[str]:
        """Extract key findings from analysis (simplified)"""
        # Split into sentences and take meaningful ones
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 50]
        return sentences[:3]  # Top 3 findings
    
    async def _generate_comparison_summary(
        self,
        comparisons: List[VendorComparison],
        aspects: List[str]
    ) -> Dict:
        """Generate overall comparison summary"""
        
        vendor_names = [c.vendor_name for c in comparisons]
        
        prompt = f"""Compare these vendors based on the analysis:

Vendors: {', '.join(vendor_names)}
Aspects analyzed: {', '.join(aspects)}

Comparison data:
{self._format_comparison_data(comparisons)}

Provide:
1. A concise summary highlighting key differences
2. A recommendation (which vendor is preferable and why, or if they're comparable)

Keep the response brief and actionable."""
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a vendor risk analyst providing comparison summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        # Simple split of summary and recommendation
        parts = content.split('Recommendation:', 1)
        summary = parts[0].replace('Summary:', '').strip()
        recommendation = parts[1].strip() if len(parts) > 1 else None
        
        return {
            "summary": summary,
            "recommendation": recommendation
        }
    
    def _format_comparison_data(self, comparisons: List[VendorComparison]) -> str:
        """Format comparison data for LLM"""
        formatted = []
        for comp in comparisons:
            formatted.append(f"""
{comp.vendor_name}:
- Security: {comp.security_score}
- Privacy: {comp.privacy_score}
- Risk Level: {comp.risk_level}
- Compliance: {', '.join(f"{k}: {v}" for k, v in comp.compliance_status.items())}
- Key Findings: {'; '.join(comp.key_findings[:2])}
            """)
        return '\n'.join(formatted)