import logging
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

_client = None

def _get_client():
    """Initialize and return the Azure OpenAI client (lazy singleton)."""
    global _client
    if _client is None:
        try:
            logger.info("Initializing Azure OpenAI client")
            
            # Validate required environment variables
            required_vars = ["AZURE_OPENAI_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            
            if missing_vars:
                error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            _client = AzureOpenAI(
                api_key=os.environ["AZURE_OPENAI_KEY"],
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                api_version="2024-02-15-preview",
            )
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            raise
    return _client

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
    """Call Azure OpenAI with the question and sources to get a regulated answer.
    
    Args:
        question: User's regulatory question
        sources: Retrieved source documents to use for answering
        
    Returns:
        LLM response with answer and citations
        
    Raises:
        ValueError: If inputs are invalid
        Exception: If API call fails
    """
    try:
        # Validate inputs
        if not question or not question.strip():
            logger.error("Empty question provided to call_llm")
            raise ValueError("Question cannot be empty")
        
        if not sources or not sources.strip():
            logger.warning("Empty sources provided to call_llm")
            raise ValueError("Sources cannot be empty")
        
        logger.info(f"Calling LLM - question length: {len(question)}, sources length: {len(sources)}")
        
        client = _get_client()
        deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
        
        logger.debug(f"Using deployment: {deployment}")
        
        resp = client.chat.completions.create(
            model=deployment,
            temperature=0.0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question:\n{question}\n\nSources:\n{sources}"},
            ],
        )
        
        answer = resp.choices[0].message.content.strip()
        logger.info(f"LLM response received - length: {len(answer)}")
        logger.debug(f"Token usage - prompt: {resp.usage.prompt_tokens}, completion: {resp.usage.completion_tokens}, total: {resp.usage.total_tokens}")
        
        return answer
    
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}", exc_info=True)
        raise Exception(f"Azure OpenAI API error: {str(e)}")
