"""
Configuration management for LLaMA 3 model parameters.

This module provides the LLaMAConfig dataclass for managing LLaMA 3 model
configuration parameters loaded from environment variables.
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLaMAConfig:
    """LLaMA 3 model configuration parameters."""
    
    model: str = "llama3"  # Ollama model name
    base_url: str = "http://localhost:11434"  # Ollama server URL
    max_tokens: int = 500  # Maximum tokens in response
    temperature: float = 0.3  # Lower temperature for more focused summaries
    enable_fallback: bool = True  # Enable regex fallback on errors
    max_transcript_chars: int = 50000  # Maximum transcript length
    request_timeout: int = 120  # Request timeout in seconds (LLaMA can be slower)
    max_retries: int = 3  # Maximum retry attempts
    
    @classmethod
    def from_env(cls) -> "LLaMAConfig":
        """
        Load configuration from environment variables with defaults.
        
        Environment Variables:
            LLAMA_MODEL: LLaMA model name (default: llama3)
            LLAMA_BASE_URL: Ollama server URL (default: http://localhost:11434)
            LLAMA_MAX_TOKENS: Maximum response tokens (default: 500)
            LLAMA_TEMPERATURE: Temperature for generation (default: 0.3)
            LLAMA_ENABLE_FALLBACK: Enable fallback mode (default: true)
            LLAMA_MAX_TRANSCRIPT_CHARS: Maximum transcript length (default: 50000)
            LLAMA_REQUEST_TIMEOUT: Request timeout in seconds (default: 120)
            LLAMA_MAX_RETRIES: Maximum retry attempts (default: 3)
        
        Returns:
            LLaMAConfig instance with values from environment or defaults
        """
        return cls(
            model=os.getenv("LLAMA_MODEL", "llama3"),
            base_url=os.getenv("LLAMA_BASE_URL", "http://localhost:11434"),
            max_tokens=int(os.getenv("LLAMA_MAX_TOKENS", "500")),
            temperature=float(os.getenv("LLAMA_TEMPERATURE", "0.3")),
            enable_fallback=os.getenv("LLAMA_ENABLE_FALLBACK", "true").lower() == "true",
            max_transcript_chars=int(os.getenv("LLAMA_MAX_TRANSCRIPT_CHARS", "50000")),
            request_timeout=int(os.getenv("LLAMA_REQUEST_TIMEOUT", "120")),
            max_retries=int(os.getenv("LLAMA_MAX_RETRIES", "3")),
        )
    
    def validate(self) -> None:
        """
        Validate configuration parameters and log warnings for invalid values.
        """
        # Validate model
        valid_models = ["llama3", "llama3:8b", "llama3:70b", "llama3.1", "llama3.1:8b", "llama3.1:70b"]
        if self.model not in valid_models:
            logger.warning(
                f"Model '{self.model}' may not be available. "
                f"Common models: {', '.join(valid_models[:3])}"
            )
        
        # Validate base URL
        if not self.base_url.startswith(("http://", "https://")):
            logger.warning(
                f"base_url '{self.base_url}' should start with http:// or https://. "
                f"Using default http://localhost:11434."
            )
            self.base_url = "http://localhost:11434"
        
        # Validate token parameters
        if self.max_tokens <= 0:
            logger.warning(
                f"max_tokens ({self.max_tokens}) must be positive. Using default 500."
            )
            self.max_tokens = 500
        
        if self.temperature < 0 or self.temperature > 2:
            logger.warning(
                f"temperature ({self.temperature}) should be between 0 and 2. "
                f"Using default 0.3."
            )
            self.temperature = 0.3
        
        # Validate transcript parameters
        if self.max_transcript_chars <= 0:
            logger.warning(
                f"max_transcript_chars ({self.max_transcript_chars}) must be positive. "
                f"Using default 50000."
            )
            self.max_transcript_chars = 50000
        
        # Validate timeout and retries
        if self.request_timeout <= 0:
            logger.warning(
                f"request_timeout ({self.request_timeout}) must be positive. "
                f"Using default 120."
            )
            self.request_timeout = 120
        
        if self.max_retries < 0:
            logger.warning(
                f"max_retries ({self.max_retries}) must be non-negative. "
                f"Using default 3."
            )
            self.max_retries = 3
        
        logger.info(
            f"LLaMA configuration validated: model={self.model}, "
            f"max_tokens={self.max_tokens}, temperature={self.temperature}, "
            f"enable_fallback={self.enable_fallback}, "
            f"request_timeout={self.request_timeout}s, base_url={self.base_url}"
        )