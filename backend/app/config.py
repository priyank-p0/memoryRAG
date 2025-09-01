"""Configuration module for the chat application."""

import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys (optional for testing)
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # CORS Configuration
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        env="ALLOWED_ORIGINS"
    )
    
    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="password", env="NEO4J_PASSWORD")
    
    # Caching / NLP Configuration
    enable_cache: bool = Field(default=True, env="ENABLE_CACHE")
    cache_dir: str = Field(default=".cache", env="CACHE_DIR")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    enable_spacy: bool = Field(default=False, env="ENABLE_SPACY")
    spacy_model: str = Field(default="en_core_web_sm", env="SPACY_MODEL")

    # LLM NER Configuration
    enable_llm_ner: bool = Field(default=False, env="ENABLE_LLM_NER")
    llm_ner_provider: str = Field(default="openai", env="LLM_NER_PROVIDER")
    llm_ner_model: str = Field(default="gpt-4o-mini", env="LLM_NER_MODEL")
    llm_ner_temperature: float = Field(default=0.0, env="LLM_NER_TEMPERATURE")
    llm_ner_max_reflection_passes: int = Field(default=1, env="LLM_NER_MAX_REFLECTION_PASSES")
    
    @property
    def origins_list(self) -> List[str]:
        """Convert allowed_origins string to list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()
