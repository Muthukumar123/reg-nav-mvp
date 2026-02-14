"""RAG (Retrieval-Augmented Generation) service for regulatory queries."""
import logging
from typing import List, Dict, Any, Optional

from src.services.llm_service import get_llm_service
from src.services.vector_db_service import get_vector_db_service
from src.models import (
    QueryRequest,
    QueryResponse,
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    ComplianceStatus,
    RegulationType
)

logger = logging.getLogger(__name__)


class RAGService:
    """Service for retrieval-augmented generation."""
    
    def __init__(self):
        """Initialize the RAG service."""
        self.llm_service = get_llm_service()
        self.vector_db_service = get_vector_db_service()
        logger.info("Initialized RAG service")
    
    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        """Answer a regulatory query using RAG."""
        try:
            # Prepare metadata filter if regulation types specified
            filter_metadata = None
            if request.regulation_types:
                # Convert to list of strings for filtering
                reg_type_names = [rt.value for rt in request.regulation_types]
                # Note: ChromaDB filtering syntax may vary
                # This is a simplified example
                filter_metadata = {"regulation_type": {"$in": reg_type_names}}
            
            # Retrieve relevant documents
            search_results = self.vector_db_service.search(
                query=request.question,
                n_results=request.max_results,
                filter_metadata=filter_metadata
            )
            
            # Extract retrieved documents
            documents = search_results.get("documents", [[]])[0]
            metadatas = search_results.get("metadatas", [[]])[0]
            distances = search_results.get("distances", [[]])[0]
            
            if not documents:
                return QueryResponse(
                    answer="I don't have enough information to answer this question. Please ensure relevant regulatory documents have been ingested.",
                    confidence=0.0,
                    sources=[],
                    regulation_types=[]
                )
            
            # Build context from retrieved documents
            context = self._build_context(documents, metadatas)
            
            # Build prompt for LLM
            system_message = self._build_system_message()
            prompt = self._build_query_prompt(request.question, context)
            
            # Generate response
            answer = await self.llm_service.generate_response(
                prompt=prompt,
                system_message=system_message
            )
            
            # Calculate confidence based on retrieval distances
            confidence = self._calculate_confidence(distances)
            
            # Build sources
            sources = []
            if request.include_references:
                sources = self._build_sources(documents, metadatas, distances)
            
            # Extract regulation types from sources
            regulation_types = list(set([
                RegulationType(meta.get("regulation_type", RegulationType.OTHER))
                for meta in metadatas
                if meta.get("regulation_type")
            ]))
            
            return QueryResponse(
                answer=answer,
                confidence=confidence,
                sources=sources,
                regulation_types=regulation_types
            )
        
        except Exception as e:
            logger.error(f"Error answering query: {str(e)}", exc_info=True)
            return QueryResponse(
                answer=f"An error occurred while processing your query: {str(e)}",
                confidence=0.0,
                sources=[],
                regulation_types=[]
            )
    
    async def check_compliance(
        self,
        request: ComplianceCheckRequest
    ) -> ComplianceCheckResponse:
        """Check compliance of a scenario against regulations."""
        try:
            # Prepare metadata filter if regulation types specified
            filter_metadata = None
            if request.regulation_types:
                reg_type_names = [rt.value for rt in request.regulation_types]
                filter_metadata = {"regulation_type": {"$in": reg_type_names}}
            
            # Retrieve relevant regulations
            search_results = self.vector_db_service.search(
                query=request.scenario,
                n_results=10,
                filter_metadata=filter_metadata
            )
            
            documents = search_results.get("documents", [[]])[0]
            metadatas = search_results.get("metadatas", [[]])[0]
            
            if not documents:
                return ComplianceCheckResponse(
                    status=ComplianceStatus.NOT_APPLICABLE,
                    summary="No relevant regulations found for this scenario.",
                    findings=[],
                    recommendations=[],
                    applicable_regulations=[]
                )
            
            # Build context
            context = self._build_context(documents, metadatas)
            
            # Build compliance check prompt
            system_message = self._build_compliance_system_message()
            prompt = self._build_compliance_prompt(
                request.scenario,
                context,
                request.detailed_analysis
            )
            
            # Generate compliance analysis
            analysis = await self.llm_service.generate_response(
                prompt=prompt,
                system_message=system_message,
                temperature=0.2  # Lower temperature for more consistent analysis
            )
            
            # Parse the analysis to extract structured information
            # This is simplified - in production, you'd use more sophisticated parsing
            status, summary, findings, recommendations = self._parse_compliance_analysis(
                analysis
            )
            
            # Extract applicable regulation types
            applicable_regulations = list(set([
                RegulationType(meta.get("regulation_type", RegulationType.OTHER))
                for meta in metadatas
                if meta.get("regulation_type")
            ]))
            
            return ComplianceCheckResponse(
                status=status,
                summary=summary,
                findings=findings,
                recommendations=recommendations,
                applicable_regulations=applicable_regulations
            )
        
        except Exception as e:
            logger.error(f"Error checking compliance: {str(e)}", exc_info=True)
            return ComplianceCheckResponse(
                status=ComplianceStatus.UNDER_REVIEW,
                summary=f"An error occurred during compliance check: {str(e)}",
                findings=[],
                recommendations=[],
                applicable_regulations=[]
            )
    
    def _build_context(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> str:
        """Build context string from retrieved documents."""
        context_parts = []
        for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
            reg_type = meta.get("regulation_type", "Unknown")
            title = meta.get("title", "Untitled")
            context_parts.append(f"[Source {i}] {reg_type} - {title}:\n{doc}\n")
        
        return "\n".join(context_parts)
    
    def _build_system_message(self) -> str:
        """Build system message for regulatory queries."""
        return """You are an expert EU banking regulatory advisor. Your role is to provide accurate, 
detailed, and compliant information about EU banking regulations. Always cite specific regulations 
and directives when applicable. If you're uncertain about something, clearly state that. 
Provide practical guidance while ensuring accuracy."""
    
    def _build_query_prompt(self, question: str, context: str) -> str:
        """Build prompt for answering queries."""
        return f"""Based on the following EU banking regulatory information, please answer the question.

Regulatory Context:
{context}

Question: {question}

Please provide a comprehensive answer that:
1. Directly addresses the question
2. References specific regulations and articles where applicable
3. Provides practical guidance
4. Highlights any important compliance considerations

Answer:"""
    
    def _build_compliance_system_message(self) -> str:
        """Build system message for compliance checking."""
        return """You are an expert EU banking compliance auditor. Your role is to analyze business 
scenarios against EU banking regulations and provide detailed compliance assessments. Be thorough, 
objective, and highlight both compliance risks and best practices."""
    
    def _build_compliance_prompt(
        self,
        scenario: str,
        context: str,
        detailed: bool
    ) -> str:
        """Build prompt for compliance checking."""
        detail_instruction = ""
        if detailed:
            detail_instruction = """
4. For each finding, explain:
   - The specific regulation or article
   - The compliance risk or issue
   - The potential impact
   - Recommended remediation steps"""
        
        return f"""Analyze the following business scenario for compliance with EU banking regulations.

Relevant Regulations:
{context}

Scenario to Analyze:
{scenario}

Please provide a compliance analysis that includes:
1. Overall compliance status (COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT, or UNDER_REVIEW)
2. Executive summary of compliance status
3. Key findings (both positive and areas of concern){detail_instruction}
5. Specific recommendations for ensuring full compliance

Format your response as follows:
STATUS: [status]
SUMMARY: [executive summary]
FINDINGS:
- [finding 1]
- [finding 2]
...
RECOMMENDATIONS:
- [recommendation 1]
- [recommendation 2]
...

Analysis:"""
    
    def _calculate_confidence(self, distances: List[float]) -> float:
        """Calculate confidence score based on retrieval distances."""
        if not distances:
            return 0.0
        
        # Lower distance means higher similarity
        # Convert to confidence score (0 to 1)
        avg_distance = sum(distances) / len(distances)
        # This is a simple heuristic - adjust based on your needs
        confidence = max(0.0, min(1.0, 1.0 - (avg_distance / 2.0)))
        return round(confidence, 2)
    
    def _build_sources(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        distances: List[float]
    ) -> List[Dict[str, Any]]:
        """Build source references."""
        sources = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            sources.append({
                "regulation_type": meta.get("regulation_type", "Unknown"),
                "title": meta.get("title", "Untitled"),
                "excerpt": doc[:200] + "..." if len(doc) > 200 else doc,
                "relevance_score": round(1.0 - (dist / 2.0), 2),
                "source_url": meta.get("source_url"),
                "effective_date": meta.get("effective_date")
            })
        return sources
    
    def _parse_compliance_analysis(
        self,
        analysis: str
    ) -> tuple[ComplianceStatus, str, List[Dict[str, Any]], List[str]]:
        """Parse compliance analysis from LLM response."""
        lines = analysis.strip().split("\n")
        
        status = ComplianceStatus.UNDER_REVIEW
        summary = ""
        findings = []
        recommendations = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("STATUS:"):
                status_text = line.replace("STATUS:", "").strip().upper()
                try:
                    status = ComplianceStatus[status_text]
                except KeyError:
                    # Try to find partial match
                    if "COMPLIANT" in status_text and "NON" not in status_text:
                        status = ComplianceStatus.COMPLIANT
                    elif "NON" in status_text:
                        status = ComplianceStatus.NON_COMPLIANT
                    elif "PARTIAL" in status_text:
                        status = ComplianceStatus.PARTIALLY_COMPLIANT
            
            elif line.startswith("SUMMARY:"):
                summary = line.replace("SUMMARY:", "").strip()
            
            elif line.startswith("FINDINGS:"):
                current_section = "findings"
            
            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
            
            elif line.startswith("-") and current_section:
                item = line[1:].strip()
                if current_section == "findings" and item:
                    findings.append({"description": item})
                elif current_section == "recommendations" and item:
                    recommendations.append(item)
        
        # If summary is empty, use first part of analysis
        if not summary:
            summary = " ".join(analysis.split("\n")[:3])
        
        return status, summary, findings, recommendations


# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
