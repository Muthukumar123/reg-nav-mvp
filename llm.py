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

Model: gpt-4-turbo
Temperature: 0.2 (low - practical, factual, low hallucination)
Max Tokens: 1024 (enough for detailed regulatory answers)

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
"""

import logging
import os
import sys
from dotenv import load_dotenv

# Configure logging for this module
logger = logging.getLogger(__name__)

# Load environment variables from .env file at module import time
load_dotenv()

# Module-level singleton for Azure OpenAI client
_client = None


def _get_client():
    """Initialize and return the Azure OpenAI client using lazy singleton pattern."""
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
            
            # Import here to ensure .env is loaded first
            from openai import AzureOpenAI
            
            # Initialize Azure OpenAI client
            _client = AzureOpenAI(
                api_key=os.environ["AZURE_OPENAI_KEY"],
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_version="2024-05-01-preview",
            )
            logger.info("Azure OpenAI client initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}", exc_info=True)
            raise
    return _client


# System prompt for the LLM
SYSTEM_PROMPT = """You are a Regulation Navigator for a bank.

Rules:
- Use ONLY the provided Sources text.
- Do NOT use any outside knowledge.
- If Sources do not contain the answer, reply exactly: NOT FOUND IN SOURCES.
- Keep the answer under 120 words.
- Always include a short Citations line listing DOC (SECTION) you used.

Format:
Answer: [your answer]
Citations: DOC (SECTION), DOC (SECTION)
"""


def call_llm(question: str, sources: str) -> str:
    """Call Azure OpenAI LLM to generate answer based on retrieved sources.
    
    Args:
        question (str): User's regulatory compliance question
        sources (str): Retrieved regulatory source chunks
        
    Returns:
        str: LLM-generated answer text with citations
        
    Raises:
        ValueError: If question or sources are empty
        Exception: If Azure OpenAI API call fails
    """
    try:
        # Input validation
        if not question or not question.strip():
            logger.error("Empty question provided to call_llm")
            raise ValueError("Question cannot be empty")
        
        if not sources or not sources.strip():
            logger.warning("Empty sources provided to call_llm")
            raise ValueError("Sources cannot be empty")
        
        logger.info(f"Calling LLM - question length: {len(question)}, sources length: {len(sources)}")
        
        # Get Azure OpenAI client
        client = _get_client()
        deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
        logger.debug(f"Using Azure deployment: {deployment}")
        
        # Call Azure OpenAI API
        logger.debug("Sending request to Azure OpenAI API")
        resp = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question:\n{question}\n\nSources:\n{sources}"},
            ],
            max_completion_tokens=1024,
        )
        
        # Extract answer text from response
        answer = resp.choices[0].message.content.strip()
        logger.info(f"LLM response received - length: {len(answer)} chars")
        logger.debug(
            f"Token usage - prompt: {resp.usage.prompt_tokens} + "
            f"completion: {resp.usage.completion_tokens} = "
            f"total: {resp.usage.total_tokens}"
        )
        
        return answer
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}", exc_info=True)
        raise Exception(f"Azure OpenAI API error: {str(e)}")

