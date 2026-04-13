"""Configuration management for the Autonomous Blog Agent."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Config(BaseSettings):
    """Application configuration with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Medium API Configuration
    medium_api_token: str = Field(
        default="",
        description="Medium API token for publishing (optional, leave empty for local drafts)"
    )
    medium_author_id: str = Field(
        default="",
        description="Medium author ID (optional, can be fetched from API)"
    )
    
    # Local Draft Configuration
    local_drafts_dir: str = Field(
        default="drafts",
        description="Directory to save local draft blog posts"
    )
    publish_to_medium: bool = Field(
        default=False,
        description="Whether to publish to Medium (requires valid API token)"
    )

    # DEV.to Configuration
    devto_api_token: str = Field(
        default="",
        description="DEV.to API token for publishing (optional, leave empty for local drafts)"
    )
    publish_to_devto: bool = Field(
        default=False,
        description="Whether to publish to DEV.to (requires valid API token)"
    )
    
    # Ollama Configuration
    ollama_endpoint: str = Field(
        default="http://localhost:11434",
        description="Ollama API endpoint URL"
    )
    ollama_model: str = Field(
        default="gemma:7b",
        description="Ollama model name for content generation"
    )
    ollama_api_key: str = Field(
        default="",
        description="Ollama API key for cloud endpoints (optional)"
    )
    ollama_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation (0.0-2.0)"
    )
    ollama_max_tokens: int = Field(
        default=2000,
        gt=0,
        description="Maximum tokens for LLM generation"
    )
    ollama_timeout: int = Field(
        default=120,
        gt=0,
        description="Timeout for Ollama requests in seconds"
    )
    
    # Crawler Configuration
    crawler_start_url: str = Field(
        default="https://blog.bytebytego.com",
        description="Starting URL for web crawling"
    )
    crawler_max_actions: int = Field(
        default=50,
        gt=0,
        description="Maximum actions per crawl session"
    )
    crawler_headless: bool = Field(
        default=True,
        description="Run browser in headless mode"
    )
    
    # Memory System Configuration
    memory_index_path: str = Field(
        default="memory/vectors.index",
        description="Path to FAISS index file"
    )
    memory_metadata_path: str = Field(
        default="memory/metadata.json",
        description="Path to metadata JSON file"
    )
    duplicate_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Cosine similarity threshold for duplicate detection"
    )
    
    # Review Configuration
    review_similarity_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for originality review"
    )
    
    # Content Generation Configuration
    min_word_count: int = Field(
        default=800,
        gt=0,
        description="Minimum word count for blog posts"
    )
    max_word_count: int = Field(
        default=1500,
        gt=0,
        description="Maximum word count for blog posts"
    )
    max_regeneration_attempts: int = Field(
        default=2,
        ge=0,
        description="Maximum regeneration attempts per content item"
    )
    
    # Retry Configuration
    max_retry_attempts: int = Field(
        default=3,
        gt=0,
        description="Maximum retry attempts for network operations"
    )
    retry_base_delay: float = Field(
        default=1.0,
        gt=0.0,
        description="Base delay for exponential backoff in seconds"
    )
    retry_max_delay: float = Field(
        default=60.0,
        gt=0.0,
        description="Maximum delay for exponential backoff in seconds"
    )
    
    # Scheduler Configuration
    schedule_time: str = Field(
        default="09:00",
        description="Daily execution time (HH:MM format)"
    )
    schedule_enabled: bool = Field(
        default=True,
        description="Enable scheduled execution"
    )
    
    # API Server Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    api_port: int = Field(
        default=8000,
        gt=0,
        lt=65536,
        description="API server port"
    )
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log output format"
    )
    
    @field_validator("medium_api_token")
    @classmethod
    def validate_medium_token(cls, v: str) -> str:
        """Validate Medium API token format (can be empty for local drafts)."""
        return v.strip()
    
    @field_validator("schedule_time")
    @classmethod
    def validate_schedule_time(cls, v: str) -> str:
        """Validate schedule time format (HH:MM)."""
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("Schedule time must be in HH:MM format")
        try:
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time values")
        except ValueError:
            raise ValueError("Schedule time must be in HH:MM format with valid values")
        return v
    
    @field_validator("min_word_count", "max_word_count")
    @classmethod
    def validate_word_counts(cls, v: int, info) -> int:
        """Validate word count constraints."""
        if info.field_name == "max_word_count" and hasattr(info.data, "min_word_count"):
            if v < info.data.get("min_word_count", 0):
                raise ValueError("max_word_count must be greater than min_word_count")
        return v


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment."""
    global _config
    _config = Config()
    return _config
