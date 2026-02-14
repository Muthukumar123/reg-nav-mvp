"""
Azure OpenAI LLM implementation.

Concrete implementation of LanguageModel interface.
Handles all communication with Azure OpenAI service.
"""

import logging
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

from core.interfaces import LanguageModel

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AzureOpenAIModel(LanguageModel):
    """Azure OpenAI language model for compliance answer synthesis.
    
    - Single Responsibility: Only handles LLM calls and response generation
    - Open/Closed: Can be replaced with other LLM providers
    - Handles all Azure-specific configuration and authentication
    """
    
    def __init__(self):
        """Initialize Azure OpenAI client with environment configuration."""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize and validate Azure OpenAI client.
        
        Raises:
            ValueError: If required environment variables are missing
        """
        required_vars = ["AZURE_OPENAI_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
        missing = [v for v in required_vars if not os.environ.get(v)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        try:
            self.client = AzureOpenAI(
                api_key=os.environ["AZURE_OPENAI_KEY"],
                api_version="2024-02-15-preview",
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
            )
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI: {str(e)}")
            raise
    
    def generate_answer(self, question: str, context: str) -> str:
        """Generate compliance answer using Azure OpenAI.
        
        Args:
            question: The compliance question
            context: Retrieved regulatory text as context
            
        Returns:
            LLM-generated compliance answer with citations
            
        Raises:
            RuntimeError: If LLM service fails
            ValueError: If inputs are invalid
        """
        if not self.client:
            raise RuntimeError("LLM client not initialized")
        
        if not question or not context:
            raise ValueError("Question and context cannot be empty")
        
        # Compliance-focused system prompt
        system_prompt = """You are an expert regulatory compliance advisor. Your task is to answer compliance questions using ONLY the provided regulatory text.

CRITICAL RULES:
1. Only use information from the provided sources
2. Always cite which article you're referencing
3. Never make up regulations or requirements
4. If the answer is not in the sources, say "This information is not covered in the provided regulations"
5. Be precise and formal in compliance language

Format your answer with inline citations like: "Article 5 states that..."
"""
        
        user_prompt = f"""Question: {question}

Available Regulatory Sources:
{context}

Please provide the most accurate compliance answer based on these sources."""
        
        try:
            logger.info(f"Calling Azure OpenAI for question: {question[:50]}...")
            
            response = self.client.chat.completions.create(
                model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3  # Low temperature for factual responses
            )
            
            answer = response.choices[0].message.content
            logger.info("LLM call successful")
            return answer
            
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise RuntimeError(f"Failed to generate answer: {str(e)}")
