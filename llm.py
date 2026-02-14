"""
Azure OpenAI LLM Integration Module

LLM ARCHITECTURE & DESIGN
==========================

This module handles integration with Azure OpenAI's gpt-4-turbo model.
It is called AFTER retrieval (see app.py for data retrieval).

TWO-STAGE RAG SYSTEM
====================

1. RETRIEVAL STAGE (app.py)
   - TF-IDF vectorization of regulatory data.txt
   - Cosine similarity search
   - Returns top_k relevant chunks + scores

2. GENERATION STAGE (this module)
   - Take question + retrieved chunks
   - Call Azure OpenAI LLM to generate answer
   - LLM reads chunks as context (in-context learning)
   - Return structured answer with citations

HOW LLM IS USED (In-Context Learning, NOT Fine-Tuning)
=====================================================

This is NOT fine-tuning or RAG fine-tuning.
This is in-context learning:
- The LLM is NOT trained on regulatory data
- The LLM IS given retrieved chunks as "context"
- The LLM reads the context and answers based on it
- Citations come directly from the retrieved chunks

Example:
```
System: "You are a regulatory expert. Use ONLY the provided Sources."
Context: "[GDPR | Article 5]\nPersonal data shall be processed lawfully..."
Question: "What is GDPR?"
LLM Response: "GDPR is... [per Article 5]"
```

WHY THIS APPROACH
=================

✓ No model training/fine-tuning needed
✓ Uses latest GPT-4 model (better reasoning)
✓ Can update sources without retraining
✓ Reduces hallucination (forced to cite sources)
✓ Clear audit trail (can trace every answer to sources)
✓ Cost-effective (pay per API call, not per training)

CONFIGURATION
=============

Model: gpt-4-turbo-preview
Temperature: 0.2 (low - practical, factual, low hallucination)
Max Tokens: 1024 (enough for detailed regulatory answers)
Timeout: 30 seconds (safety timeout)

Environment Variables (Required):
- AZURE_OPENAI_KEY: API key
- AZURE_OPENAI_ENDPOINT: https://your-instance.openai.azure.com/
- AZURE_OPENAI_DEPLOYMENT: your-deployment-name

SYSTEM PROMPT
=============

The LLM is given strict instructions:
- Use ONLY the provided Sources (retrieved chunks)
- Do NOT use outside knowledge
- If no answer in Sources, say "NOT FOUND IN SOURCES"
- Keep answers concise (< 120 words)

This prevents hallucination by forcing the LLM to:
1. Read the retrieved regulatory text
2. Generate answer based only on that text
3. Cite the sources it used
4. Refuse if sources don't contain the answer

Provides client initialization and API calls to Azure OpenAI service.
Handles authentication, error handling, and LLM response formatting.

Features:
- Lazy singleton pattern for client initialization
- Environment variable validation
- Comprehensive error handling and logging
- Token usage tracking for monitoring
"""

import logging
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Configure logging for this module
logger = logging.getLogger(__name__)

# Load environment variables from .env file at module import time
# This must happen before accessing environment variables
load_dotenv()

_client = None  # Module-level singleton for Azure OpenAI client


def _get_client():
    """Initialize and return the Azure OpenAI client using lazy singleton pattern.
    
    DEPENDENCY INJECTION & LAZY INITIALIZATION
    ===========================================
    
    This uses the lazy singleton pattern:
    - Client created on FIRST CALL to _get_client()
    - Not created during module import
    - Cached for reuse in subsequent calls
    - Benefits:
      * Delays errors until client is actually needed
      * Allows changing credentials before first use
      * Thread-safe for most use cases
    
    On first call, validates that all required environment variables are set,
    then creates and caches the client for subsequent calls. This approach:
    - Defers initialization until actually needed (lazy loading)
    - Prevents client creation errors from affecting imports
    - Ensures single client instance across the application
    
    Required environment variables:
    - AZURE_OPENAI_KEY: API authentication key
    - AZURE_OPENAI_ENDPOINT: Azure service endpoint (https://...)
    - AZURE_OPENAI_DEPLOYMENT: Model deployment name
    
    Returns:
        AzureOpenAI: Authenticated Azure OpenAI client instance
        
    Raises:
        ValueError: If required environment variables are missing
        Exception: If client initialization fails
    """
    global _client
    if _client is None:
        try:
            logger.info("Initializing Azure OpenAI client (lazy singleton)")
            
            # Validate required environment variables
            required_vars = ["AZURE_OPENAI_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            
            if missing_vars:
                error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Initialize Azure OpenAI client with required parameters
            # Note: Using explicit parameters to avoid version compatibility issues
            try:
                _client = AzureOpenAI(
                    api_key=os.environ["AZURE_OPENAI_KEY"],
                    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                    api_version="2024-02-15-preview",
                    timeout=30.0,  # Add explicit timeout for safety
                    max_retries=2,  # Add retry configuration for resilience
                )
                logger.info("Azure OpenAI client initialized successfully")
            except TypeError as te:
                # Handle version compatibility issues with certain parameters
                logger.warning(f"Retrying client initialization with basic parameters: {str(te)}")
                _client = AzureOpenAI(
                    api_key=os.environ["AZURE_OPENAI_KEY"],
                    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                    api_version="2024-02-15-preview",
                )
                logger.info("Azure OpenAI client initialized with basic parameters")
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            raise
    return _client


# ============================================================================
# LLM SYSTEM PROMPT: Enforces source-based answers for compliance
# ============================================================================
#
# This prompt ensures the LLM only uses retrieved documents and doesn't
# hallucinate or use external knowledge that could violate compliance.
#
# PROMPT ENGINEERING STRATEGY
# ===========================
# - Clear role: "Regulation Navigator for a bank"
# - Explicit constraints: "Use ONLY provided Sources"
# - Failure mode: "If not in Sources, say NOT FOUND"
# - Length limit: Forces concise, focused answers
# - No disclaimers: Prevents evasion ("I don't know" avoidance)

SYSTEM_PROMPT = """You are a Regulation Navigator for a bank.

Rules:
- Use ONLY the provided Sources text.
- Do NOT use any outside knowledge.
- If Sources do not contain the answer, reply exactly: NOT FOUND IN SOURCES.
- Keep the answer under 120 words.
- Always include a short Citations line listing DOC (SECTION) you used.

Format:
Answer: ...
Citations: DOC (SECTION)
"""

def call_llm(question: str, sources: str) -> str:
    """Call Azure OpenAI LLM to generate answer based on retrieved sources.
    
    LLM GENERATION STAGE (Part 2 of RAG System)
    ==========================================
    
    This function is called AFTER retrieval (see app.py).
    It takes the question + retrieved chunks and generates an answer.
    
    PROMPT STRUCTURE
    ================
    
    The LLM is given 3 messages:
    
    1. SYSTEM PROMPT (static - defines behavior)
       "You are a Regulation Navigator for a bank.
        Use ONLY the provided Sources.
        If not in Sources, say: NOT FOUND IN SOURCES."
    
    2. USER PROMPT (dynamic - the actual request)
       "Question: What is GDPR?
        
        Sources:
        [GDPR | Article 5]
        Personal data shall be processed lawfully...
        
        [GDPR | Article 6]
        Processing shall be lawful only if..."
    
    This structure forces the LLM to:
    - Read the Retrieved Sources
    - Generate answer based on Contents
    - Include citations (from sources)
    - Refuse if sources don't have answer
    
    LLM CONFIGURATION
    =================
    
    Model: gpt-4-turbo-preview (state-of-the-art reasoning)
    Temperature: 0.2 (low randomness = practical, factual)
    - 0.0: Deterministic (same answer every time)
    - 0.7+: Creative (varied responses)
    - 0.2: Sweet spot for compliance (factual but human-like)
    
    Timeout: 30 seconds (safety limit)
    Max Retries: 2 (resilience for transient errors)
    Max Tokens: 1024 (enough for detailed regulatory answers)
    
    RESPONSE HANDLING
    =================
    
    Raw LLM Response:
    {
        "choices": [
            {
                "message": {
                    "content": "GDPR is Regulation (EU) 2016/679..."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 250,
            "completion_tokens": 75,
            "total_tokens": 325
        }
    }
    
    Parsed Output: Just the answer string from message.content
    
    ERROR HANDLING
    ==============
    
    Errors caught:
    - Empty question/sources (ValueError)
    - Authentication failures (invalid API key)
    - Rate limiting (too many requests)
    - Network timeouts (server slow)
    - Invalid responses (malformed JSON)
    
    All errors logged and re-raised for caller to handle
    
    Args:
        question (str): User's regulatory compliance question
                       Example: "What is GDPR?"
                       Passed to LLM for analysis
        
        sources (str): Retrieved regulatory source chunks (from TF-IDF retrieval)
                      Format: "[DOC | Section]\ntext\n\n[DOC | Section]\ntext"
                      Example: "[GDPR | Article 5]\nPersonal data shall..."
                      Used by LLM as context for answer generation
        
    Returns:
        str: LLM-generated answer text
             - Contains full answer + citations
             - If sources don't have answer: "NOT FOUND IN SOURCES."
             - Always based on provided sources (not external knowledge)
        
    Raises:
        ValueError: If question or sources are empty
        Exception: If Azure OpenAI API call fails
    """
    try:
        # ====== INPUT VALIDATION ======
        # Ensure inputs are valid before calling expensive LLM API
        if not question or not question.strip():
            logger.error("Empty question provided to call_llm")
            raise ValueError("Question cannot be empty")
        
        if not sources or not sources.strip():
            logger.warning("Empty sources provided to call_llm")
            raise ValueError("Sources cannot be empty")
        
        logger.info(f"Calling LLM - question length: {len(question)}, sources length: {len(sources)}")
        
        # ====== CLIENT INITIALIZATION ======
        # Get cached Azure OpenAI client (or initialize on first call)
        client = _get_client()
        deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
        logger.debug(f"Using Azure deployment: {deployment}")
        
        # ====== API CALL ======
        # Send messages to LLM with system prompt + user question + sources
        logger.debug("Sending request to Azure OpenAI API")
        resp = client.chat.completions.create(
            model=deployment,
            messages=[
                # SYSTEM PROMPT: Defines LLM behavior
                {"role": "system", "content": SYSTEM_PROMPT},
                
                # USER MESSAGE: Question + Retrieved Sources
                # Format: "Question: ...\n\nSources: ..."
                {"role": "user", "content": f"Question:\n{question}\n\nSources:\n{sources}"},
            ],
            temperature=0.2,     # Low temp = factual, practical (not creative)
            max_tokens=1024,     # Limit response length
            timeout=30.0,        # Safety timeout
        )
        
        # ====== RESPONSE PARSING ======
        # Extract answer text from LLM response
        answer = resp.choices[0].message.content.strip()
        logger.info(f"LLM response received - length: {len(answer)} chars")
        
        # ====== TOKEN TRACKING ======
        # Log token usage for monitoring (costs, performance)
        logger.debug(
            f"Token usage - "
            f"prompt: {resp.usage.prompt_tokens} + "
            f"completion: {resp.usage.completion_tokens} = "
            f"total: {resp.usage.total_tokens}"
        )
        
        return answer
    
    except ValueError:
        # Re-raise validation errors (empty inputs)
        raise
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}", exc_info=True)
        raise Exception(f"Azure OpenAI API error: {str(e)}")
