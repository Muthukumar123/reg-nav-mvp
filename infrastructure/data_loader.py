"""
Regulatory data loader implementation.

Concrete implementation of DataLoader interface.
Handles parsing regulatory documents in standard format.
"""

import logging
from typing import List
from pathlib import Path

from core.interfaces import DataLoader
from core.entities import RegulatoryChunk

logger = logging.getLogger(__name__)


class RegulatoryDocumentLoader(DataLoader):
    """Loads regulatory documents from text files.
    
    - Single Responsibility: Only handles document parsing
    - Open/Closed: Can extend to support different formats (XML, PDF, etc)
    - Format: [DOC] NAME | SECTION followed by text content
    """
    
    CHUNK_HEADER_PREFIX = "[DOC]"
    SECTION_DELIMITER = "|"
    MIN_CHUNK_LENGTH = 30  # Minimum chars for valid chunk
    
    def load(self, source: str) -> List[RegulatoryChunk]:
        """Load regulatory chunks from file.
        
        Args:
            source: Path to regulatory document file
            
        Returns:
            List of parsed RegulatoryChunk objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(source)
        
        if not path.exists():
            raise FileNotFoundError(f"Regulatory document not found: {source}")
        
        if not path.is_file():
            raise ValueError(f"Source must be a file: {source}")
        
        logger.info(f"Loading regulatory documents from {source}")
        chunks = []
        current_chunk = None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Check for chunk header
                    if line.startswith(self.CHUNK_HEADER_PREFIX):
                        # Save previous chunk if exists
                        if current_chunk and len(current_chunk["text"]) >= self.MIN_CHUNK_LENGTH:
                            chunks.append(self._create_chunk(current_chunk))
                        
                        # Parse new header: [DOC] NAME | SECTION
                        header = line[len(self.CHUNK_HEADER_PREFIX):].strip()
                        parts = [p.strip() for p in header.split(self.SECTION_DELIMITER)]
                        
                        current_chunk = {
                            "doc": parts[0] if len(parts) > 0 else "UNKNOWN_DOC",
                            "section": parts[1] if len(parts) > 1 else "UNKNOWN_SECTION",
                            "text": ""
                        }
                    else:
                        # Accumulate text for current chunk
                        if current_chunk:
                            current_chunk["text"] += line + " "
            
            # Don't forget last chunk
            if current_chunk and len(current_chunk["text"]) >= self.MIN_CHUNK_LENGTH:
                chunks.append(self._create_chunk(current_chunk))
            
            logger.info(f"Successfully loaded {len(chunks)} regulatory chunks from {source}")
            return chunks
            
        except IOError as e:
            logger.error(f"Failed to read regulatory document: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Invalid chunk format: {str(e)}")
            raise
    
    def _create_chunk(self, chunk_data: dict) -> RegulatoryChunk:
        """Create validated RegulatoryChunk from parsed data.
        
        Args:
            chunk_data: Dictionary with doc, section, text
            
        Returns:
            RegulatoryChunk entity
            
        Raises:
            ValueError: If chunk data is invalid
        """
        try:
            return RegulatoryChunk(
                doc=chunk_data["doc"],
                section=chunk_data["section"],
                text=chunk_data["text"].strip()
            )
        except ValueError as e:
            logger.warning(f"Skipping invalid chunk: {str(e)}")
            raise
