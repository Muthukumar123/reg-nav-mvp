"""Data models for the EU Banking Regulator LLM system."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class RegulationType(str, Enum):
    """Types of EU banking regulations."""
    CRD = "Capital Requirements Directive"
    CRR = "Capital Requirements Regulation"
    MiFID = "Markets in Financial Instruments Directive"
    GDPR = "General Data Protection Regulation"
    AML = "Anti-Money Laundering Directive"
    PSD2 = "Payment Services Directive 2"
    EMIR = "European Market Infrastructure Regulation"
    BRRD = "Bank Recovery and Resolution Directive"
    SSM = "Single Supervisory Mechanism"
    SRM = "Single Resolution Mechanism"
    OTHER = "Other"


class ComplianceStatus(str, Enum):
    """Compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    NOT_APPLICABLE = "not_applicable"


class RegulatoryDocument(BaseModel):
    """Model for a regulatory document."""
    id: str
    title: str
    regulation_type: RegulationType
    effective_date: Optional[datetime] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    """Request model for regulatory queries."""
    question: str = Field(..., description="The regulatory question to ask")
    regulation_types: Optional[List[RegulationType]] = Field(
        None,
        description="Filter by specific regulation types"
    )
    include_references: bool = Field(
        True,
        description="Include source references in the response"
    )
    max_results: int = Field(
        5,
        description="Maximum number of relevant documents to retrieve",
        ge=1,
        le=20
    )


class QueryResponse(BaseModel):
    """Response model for regulatory queries."""
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    regulation_types: List[RegulationType] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComplianceCheckRequest(BaseModel):
    """Request model for compliance checking."""
    scenario: str = Field(..., description="The business scenario to check")
    regulation_types: Optional[List[RegulationType]] = Field(
        None,
        description="Specific regulations to check against"
    )
    detailed_analysis: bool = Field(
        True,
        description="Include detailed compliance analysis"
    )


class ComplianceCheckResponse(BaseModel):
    """Response model for compliance checking."""
    status: ComplianceStatus
    summary: str
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    applicable_regulations: List[RegulationType] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DocumentIngestionRequest(BaseModel):
    """Request model for ingesting regulatory documents."""
    file_path: str
    regulation_type: RegulationType
    title: Optional[str] = None
    effective_date: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentIngestionResponse(BaseModel):
    """Response model for document ingestion."""
    success: bool
    document_id: Optional[str] = None
    message: str
    chunks_created: int = 0
