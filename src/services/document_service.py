"""Document ingestion service for regulatory documents."""
import os
import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from PyPDF2 import PdfReader
from docx import Document

from src.services.vector_db_service import get_vector_db_service
from src.models import (
    DocumentIngestionRequest,
    DocumentIngestionResponse,
    RegulatoryDocument,
    RegulationType
)

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """Service for ingesting regulatory documents."""
    
    def __init__(self):
        """Initialize the document ingestion service."""
        self.vector_db_service = get_vector_db_service()
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
        logger.info("Initialized Document Ingestion service")
    
    def ingest_document(
        self,
        request: DocumentIngestionRequest
    ) -> DocumentIngestionResponse:
        """Ingest a regulatory document."""
        try:
            # Check if file exists
            if not os.path.exists(request.file_path):
                return DocumentIngestionResponse(
                    success=False,
                    message=f"File not found: {request.file_path}",
                    chunks_created=0
                )
            
            # Extract text based on file type
            text = self._extract_text(request.file_path)
            
            if not text:
                return DocumentIngestionResponse(
                    success=False,
                    message="No text could be extracted from the document",
                    chunks_created=0
                )
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Create document metadata
            title = request.title or os.path.basename(request.file_path)
            
            # Chunk the text
            chunks = self._chunk_text(text)
            
            # Prepare chunks with metadata
            chunk_ids = []
            chunk_texts = []
            chunk_metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk)
                
                metadata = {
                    "document_id": doc_id,
                    "chunk_index": i,
                    "title": title,
                    "regulation_type": request.regulation_type.value,
                    "file_path": request.file_path,
                    **request.metadata
                }
                
                if request.effective_date:
                    metadata["effective_date"] = request.effective_date.isoformat()
                
                chunk_metadatas.append(metadata)
            
            # Add to vector database
            self.vector_db_service.add_documents(
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )
            
            logger.info(
                f"Successfully ingested document: {title} "
                f"({len(chunks)} chunks)"
            )
            
            return DocumentIngestionResponse(
                success=True,
                document_id=doc_id,
                message=f"Successfully ingested document: {title}",
                chunks_created=len(chunks)
            )
        
        except Exception as e:
            logger.error(f"Error ingesting document: {str(e)}", exc_info=True)
            return DocumentIngestionResponse(
                success=False,
                message=f"Error ingesting document: {str(e)}",
                chunks_created=0
            )
    
    def ingest_text(
        self,
        text: str,
        title: str,
        regulation_type: RegulationType,
        metadata: Dict[str, Any] = None
    ) -> DocumentIngestionResponse:
        """Ingest text directly without file."""
        try:
            if not text:
                return DocumentIngestionResponse(
                    success=False,
                    message="No text provided",
                    chunks_created=0
                )
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Chunk the text
            chunks = self._chunk_text(text)
            
            # Prepare chunks with metadata
            chunk_ids = []
            chunk_texts = []
            chunk_metadatas = []
            
            base_metadata = metadata or {}
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk)
                
                chunk_metadata = {
                    "document_id": doc_id,
                    "chunk_index": i,
                    "title": title,
                    "regulation_type": regulation_type.value,
                    **base_metadata
                }
                
                chunk_metadatas.append(chunk_metadata)
            
            # Add to vector database
            self.vector_db_service.add_documents(
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )
            
            logger.info(
                f"Successfully ingested text: {title} ({len(chunks)} chunks)"
            )
            
            return DocumentIngestionResponse(
                success=True,
                document_id=doc_id,
                message=f"Successfully ingested text: {title}",
                chunks_created=len(chunks)
            )
        
        except Exception as e:
            logger.error(f"Error ingesting text: {str(e)}", exc_info=True)
            return DocumentIngestionResponse(
                success=False,
                message=f"Error ingesting text: {str(e)}",
                chunks_created=0
            )
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from a file."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == ".pdf":
            return self._extract_text_from_pdf(file_path)
        elif file_ext in [".docx", ".doc"]:
            return self._extract_text_from_docx(file_path)
        elif file_ext == ".txt":
            return self._extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise
    
    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise
    
    def _chunk_text(self, text: str) -> List[str]:
        """Chunk text into smaller pieces with overlap."""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split("\n\n")
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Start new chunk with overlap
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    # Paragraph itself is too large, split it
                    words = paragraph.split()
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk) + len(word) + 1 > self.chunk_size:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = word
                        else:
                            temp_chunk += " " + word if temp_chunk else word
                    current_chunk = temp_chunk
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


# Global document ingestion service instance
_ingestion_service: Optional[DocumentIngestionService] = None


def get_ingestion_service() -> DocumentIngestionService:
    """Get or create the global document ingestion service instance."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = DocumentIngestionService()
    return _ingestion_service
