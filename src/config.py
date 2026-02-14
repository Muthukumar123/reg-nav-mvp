"""Configuration management for the EU Banking Regulator LLM system."""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    llm_provider: str = Field("openai", alias="LLM_PROVIDER")
    llm_model: str = Field("gpt-4-turbo-preview", alias="LLM_MODEL")
    llm_temperature: float = Field(0.3, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(4096, alias="LLM_MAX_TOKENS")
    
    # Vector Database
    vector_db_path: str = Field("./data/vector_db", alias="VECTOR_DB_PATH")
    embedding_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL"
    )
    
    # API Configuration
    api_host: str = Field("0.0.0.0", alias="API_HOST")
    api_port: int = Field(8000, alias="API_PORT")
    api_reload: bool = Field(False, alias="API_RELOAD")
    
    # Regulatory Data
    regulatory_docs_path: str = Field(
        "./data/regulatory_docs",
        alias="REGULATORY_DOCS_PATH"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True


# Global settings instance
settings = Settings()
