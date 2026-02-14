"""LLM service for interacting with various LLM providers."""
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import logging

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage

from src.config import settings

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    """Abstract base class for LLM services."""
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from the LLM."""
        pass


class OpenAIService(BaseLLMService):
    """Service for OpenAI LLM."""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            openai_api_key=settings.openai_api_key
        )
        logger.info(f"Initialized OpenAI service with model: {settings.llm_model}")
    
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from OpenAI."""
        messages = []
        
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        messages.append(HumanMessage(content=prompt))
        
        # Override settings if provided
        if temperature is not None or max_tokens is not None:
            llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                openai_api_key=settings.openai_api_key
            )
            response = await llm.ainvoke(messages)
        else:
            response = await self.llm.ainvoke(messages)
        
        return response.content


class AnthropicService(BaseLLMService):
    """Service for Anthropic Claude LLM."""
    
    def __init__(self):
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        
        self.llm = ChatAnthropic(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            anthropic_api_key=settings.anthropic_api_key
        )
        logger.info(f"Initialized Anthropic service with model: {settings.llm_model}")
    
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from Anthropic Claude."""
        messages = []
        
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        messages.append(HumanMessage(content=prompt))
        
        # Override settings if provided
        if temperature is not None or max_tokens is not None:
            llm = ChatAnthropic(
                model=settings.llm_model,
                temperature=temperature or settings.llm_temperature,
                max_tokens=max_tokens or settings.llm_max_tokens,
                anthropic_api_key=settings.anthropic_api_key
            )
            response = await llm.ainvoke(messages)
        else:
            response = await self.llm.ainvoke(messages)
        
        return response.content


class LLMServiceFactory:
    """Factory for creating LLM service instances."""
    
    @staticmethod
    def create_service() -> BaseLLMService:
        """Create an LLM service based on configuration."""
        provider = settings.llm_provider.lower()
        
        if provider == "openai":
            return OpenAIService()
        elif provider == "anthropic":
            return AnthropicService()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# Global LLM service instance
_llm_service: Optional[BaseLLMService] = None


def get_llm_service() -> BaseLLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMServiceFactory.create_service()
    return _llm_service
