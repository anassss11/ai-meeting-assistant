"""
Configuration management for NVIDIA Qwen 3.5 model parameters.

This module provides the NVIDIAConfig dataclass for managing NVIDIA API
configuration parameters loaded from environment variables.
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NVIDIAConfig:
    """NVIDIA Qwen 3.5 model configuration parameters."""
    
    api_key: str = ""  # NVIDIA API key
    model: str = "qwen/qwen3.5-397b-a17b"  # Qwen 3.5 model
    base_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    max_tokens: int = 16384  # Maximum tokens in response
    temperature: float = 0.60  # Temperature for generation
    top_p: float = 0.95  # Top-p sampling
    top_k: int = 20  # Top-k sampling
    presence_penalty: float = 0.0  # Presence penalty
    repetition_penalty: float = 1.0  # Repetition penalty
    enable_fallback: bool = True  # Enable regex fallback on errors
    max_transcript_chars: int = 50000  # Maximum transcript length
    request_timeout: int = 0  # Request timeout in seconds (0 = no timeout)
    max_retries: int = 3  # Maximum retry attempts
    enable_thinking: bool = True  # Enable thinking mode
    
    @classmethod
    def from_env(cls) -> "NVIDIAConfig":
        """
        Load configuration from environment variables with defaults.
        
        Environment Variables:
            NVIDIA_API_KEY: NVIDIA API key (required)
            NVIDIA_MODEL: Model name (default: qwen/qwen3.5-397b-a17b)
            NVIDIA_MAX_TOKENS: Maximum response tokens (default: 16384)
            NVIDIA_TEMPERATURE: Temperature for generation (default: 0.60)
            NVIDIA_TOP_P: Top-p sampling (default: 0.95)
            NVIDIA_TOP_K: Top-k sampling (default: 20)
            NVIDIA_ENABLE_FALLBACK: Enable fallback mode (default: true)
            NVIDIA_MAX_TRANSCRIPT_CHARS: Maximum transcript length (default: 50000)
            NVIDIA_REQUEST_TIMEOUT: Request timeout in seconds (default: 0 = no timeout)
            NVIDIA_MAX_RETRIES: Maximum retry attempts (default: 3)
        
        Returns:
            NVIDIAConfig instance with values from environment or defaults
        """
        return cls(
            api_key=os.getenv("NVIDIA_API_KEY", ""),
            model=os.getenv("NVIDIA_MODEL", "qwen/qwen3.5-397b-a17b"),
            max_tokens=int(os.getenv("NVIDIA_MAX_TOKENS", "16384")),
            temperature=float(os.getenv("NVIDIA_TEMPERATURE", "0.60")),
            top_p=float(os.getenv("NVIDIA_TOP_P", "0.95")),
            top_k=int(os.getenv("NVIDIA_TOP_K", "20")),
            presence_penalty=float(os.getenv("NVIDIA_PRESENCE_PENALTY", "0.0")),
            repetition_penalty=float(os.getenv("NVIDIA_REPETITION_PENALTY", "1.0")),
            enable_fallback=os.getenv("NVIDIA_ENABLE_FALLBACK", "true").lower() == "true",
            max_transcript_chars=int(os.getenv("NVIDIA_MAX_TRANSCRIPT_CHARS", "50000")),
            request_timeout=int(os.getenv("NVIDIA_REQUEST_TIMEOUT", "0")),
            max_retries=int(os.getenv("NVIDIA_MAX_RETRIES", "3")),
            enable_thinking=os.getenv("NVIDIA_ENABLE_THINKING", "true").lower() == "true",
        )
    
    def validate(self) -> None:
        """
        Validate configuration parameters and log warnings for invalid values.
        """
        # Validate API key
        if not self.api_key:
            logger.error("NVIDIA_API_KEY is required but not set")
            raise ValueError("NVIDIA_API_KEY environment variable is required")
        
        # Validate token parameters
        if self.max_tokens <= 0:
            logger.warning(
                f"max_tokens ({self.max_tokens}) must be positive. Using default 16384."
            )
            self.max_tokens = 16384
        
        if self.temperature < 0 or self.temperature > 2:
            logger.warning(
                f"temperature ({self.temperature}) should be between 0 and 2. "
                f"Using default 0.60."
            )
            self.temperature = 0.60
        
        # Validate sampling parameters
        if self.top_p < 0 or self.top_p > 1:
            logger.warning(
                f"top_p ({self.top_p}) should be between 0 and 1. "
                f"Using default 0.95."
            )
            self.top_p = 0.95
        
        if self.top_k <= 0:
            logger.warning(
                f"top_k ({self.top_k}) must be positive. Using default 20."
            )
            self.top_k = 20
        
        # Validate transcript parameters
        if self.max_transcript_chars <= 0:
            logger.warning(
                f"max_transcript_chars ({self.max_transcript_chars}) must be positive. "
                f"Using default 50000."
            )
            self.max_transcript_chars = 50000
        
        # Validate timeout and retries
        if self.request_timeout < 0:
            logger.warning(
                f"request_timeout ({self.request_timeout}) must be non-negative. "
                f"Using default 0 (no timeout)."
            )
            self.request_timeout = 0
        
        if self.max_retries < 0:
            logger.warning(
                f"max_retries ({self.max_retries}) must be non-negative. "
                f"Using default 3."
            )
            self.max_retries = 3
        
        logger.info(
            f"NVIDIA configuration validated: model={self.model}, "
            f"max_tokens={self.max_tokens}, temperature={self.temperature}, "
            f"enable_fallback={self.enable_fallback}, "
            f"request_timeout={self.request_timeout}s"
        )