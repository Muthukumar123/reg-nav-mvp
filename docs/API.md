# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. For production use, implement proper authentication mechanisms.

## Endpoints

### Health Check

**GET** `/health`

Check the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "llm_provider": "openai",
  "llm_model": "gpt-4-turbo-preview",
  "vector_db": {
    "total_documents": 42,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "collection_name": "regulatory_documents"
  }
}
```

### Query Regulations

**POST** `/api/query`

Ask questions about EU banking regulations.

**Request Body:**
```json
{
  "question": "What are the capital requirements for banks?",
  "regulation_types": ["Capital Requirements Regulation"],
  "include_references": true,
  "max_results": 5
}
```

**Parameters:**
- `question` (string, required): The regulatory question
- `regulation_types` (array, optional): Filter by specific regulation types
- `include_references` (boolean, default: true): Include source references
- `max_results` (integer, default: 5, range: 1-20): Maximum documents to retrieve

**Response:**
```json
{
  "answer": "EU banks must maintain minimum capital ratios...",
  "confidence": 0.92,
  "sources": [
    {
      "regulation_type": "Capital Requirements Regulation",
      "title": "CRR Article 92",
      "excerpt": "Institutions shall at all times satisfy...",
      "relevance_score": 0.95,
      "source_url": "https://eur-lex.europa.eu/...",
      "effective_date": "2021-01-01T00:00:00"
    }
  ],
  "regulation_types": ["Capital Requirements Regulation"],
  "timestamp": "2024-02-14T10:30:00"
}
```

### Check Compliance

**POST** `/api/compliance/check`

Analyze a business scenario for regulatory compliance.

**Request Body:**
```json
{
  "scenario": "We want to launch a mobile payment app with PIN authentication",
  "regulation_types": ["Payment Services Directive 2"],
  "detailed_analysis": true
}
```

**Response:**
```json
{
  "status": "partially_compliant",
  "summary": "The mobile payment scenario requires strong customer authentication...",
  "findings": [
    {
      "description": "PSD2 requires two-factor authentication for payment initiation"
    }
  ],
  "recommendations": [
    "Implement biometric authentication as a second factor"
  ],
  "applicable_regulations": ["Payment Services Directive 2"],
  "timestamp": "2024-02-14T10:35:00"
}
```

### Ingest Document

**POST** `/api/documents/ingest`

Ingest a regulatory document into the knowledge base.

### Get Document Statistics

**GET** `/api/documents/stats`

Get statistics about ingested documents.

### Clear Documents

**DELETE** `/api/documents/clear`

Clear all documents from the knowledge base.

## Regulation Types

Available regulation types:

- Capital Requirements Directive (CRD)
- Capital Requirements Regulation (CRR)
- Markets in Financial Instruments Directive (MiFID)
- General Data Protection Regulation (GDPR)
- Anti-Money Laundering Directive (AML)
- Payment Services Directive 2 (PSD2)
- European Market Infrastructure Regulation (EMIR)
- Bank Recovery and Resolution Directive (BRRD)
- Single Supervisory Mechanism (SSM)
- Single Resolution Mechanism (SRM)
