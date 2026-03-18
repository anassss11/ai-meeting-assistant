"""
Configuration management for BART model parameters.

This module provides the BARTConfig dataclass for managing BART model
configuration parameters loaded from environment variables.
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BARTConfig:
    """BART model configuration parameters."""
    
    device: str = "cpu"  # "cpu" or "cuda"
    max_length: int = 80   # Shorter summaries for conciseness
    min_length: int = 15   # Minimum length to ensure some content
    num_beams: int = 4     # Increased for better quality
    length_penalty: float = 2.0  # Encourage shorter summaries
    early_stopping: bool = True  # Stop when all beams finish
    no_repeat_ngram_size: int = 3  # Prevent repetitive phrases
    do_sample: bool = False  # Use deterministic generation for consistency
    enable_fallback: bool = True  # Enable regex fallback on errors
    model_cache_dir: str | None = None  # Custom cache directory
    max_transcript_chars: int = 50000  # Maximum transcript length
    chunk_max_tokens: int = 512  # Reduced from 1024 for faster processing
    chunk_overlap_tokens: int = 64  # Reduced overlap
    inference_timeout: int = 0  # No timeout - let BART take as long as needed
    custom_prompt: str | None = None  # Custom instruction prompt for better summaries
    use_comprehensive_prompt: bool = False  # Use simple "Meeting summary:" prefix vs no prefix
    
    @classmethod
    def from_env(cls) -> "BARTConfig":
        """
        Load configuration from environment variables with defaults.
        
        Environment Variables:
            BART_DEVICE: cpu or cuda (default: cpu)
            BART_MAX_LENGTH: Maximum summary tokens (default: 150)
            BART_MIN_LENGTH: Minimum summary tokens (default: 40)
            BART_NUM_BEAMS: Beam search width (default: 4)
            BART_LENGTH_PENALTY: Length penalty for generation (default: 2.0)
            BART_EARLY_STOPPING: Stop when all beams finish (default: true)
            BART_ENABLE_FALLBACK: Enable fallback mode (default: true)
            BART_MODEL_CACHE_DIR: Custom model cache path (default: None)
            BART_MAX_TRANSCRIPT_CHARS: Maximum transcript length (default: 50000)
            BART_CHUNK_MAX_TOKENS: Maximum tokens per chunk (default: 1024)
            BART_CHUNK_OVERLAP_TOKENS: Overlap between chunks (default: 128)
            BART_INFERENCE_TIMEOUT: Timeout in seconds (default: 30)
        
        Returns:
            BARTConfig instance with values from environment or defaults
        """
        return cls(
            device=os.getenv("BART_DEVICE", "cpu"),
            max_length=int(os.getenv("BART_MAX_LENGTH", "150")),
            min_length=int(os.getenv("BART_MIN_LENGTH", "40")),
            num_beams=int(os.getenv("BART_NUM_BEAMS", "4")),
            length_penalty=float(os.getenv("BART_LENGTH_PENALTY", "2.0")),
            early_stopping=os.getenv("BART_EARLY_STOPPING", "true").lower() == "true",
            enable_fallback=os.getenv("BART_ENABLE_FALLBACK", "true").lower() == "true",
            model_cache_dir=os.getenv("BART_MODEL_CACHE_DIR"),
            max_transcript_chars=int(os.getenv("BART_MAX_TRANSCRIPT_CHARS", "50000")),
            chunk_max_tokens=int(os.getenv("BART_CHUNK_MAX_TOKENS", "1024")),
            chunk_overlap_tokens=int(os.getenv("BART_CHUNK_OVERLAP_TOKENS", "128")),
            inference_timeout=int(os.getenv("BART_INFERENCE_TIMEOUT", "0")),  # 0 = no timeout
            custom_prompt=os.getenv("BART_CUSTOM_PROMPT"),  # Custom instruction prompt
            use_comprehensive_prompt=os.getenv("BART_USE_COMPREHENSIVE_PROMPT", "false").lower() == "true",
        )
    
    def validate(self) -> None:
        """
        Validate configuration parameters and log warnings for invalid values.
        
        This method checks configuration parameters and adjusts invalid values
        to safe defaults while logging warnings. It validates:
        - Device is either "cpu" or "cuda"
        - max_length is greater than min_length
        - Token counts are positive
        - Timeout is positive
        - Overlap is less than max tokens per chunk
        """
        # Validate device
        if self.device not in ("cpu", "cuda"):
            logger.warning(
                f"Invalid device '{self.device}', must be 'cpu' or 'cuda'. Using 'cpu'."
            )
            self.device = "cpu"
        
        # Validate length parameters
        if self.max_length < self.min_length:
            logger.warning(
                f"max_length ({self.max_length}) < min_length ({self.min_length}). "
                f"Adjusting max_length to {self.min_length + 10}."
            )
            self.max_length = self.min_length + 10
        
        if self.min_length <= 0:
            logger.warning(
                f"min_length ({self.min_length}) must be positive. Using default 40."
            )
            self.min_length = 40
        
        if self.max_length <= 0:
            logger.warning(
                f"max_length ({self.max_length}) must be positive. Using default 150."
            )
            self.max_length = 150
        
        # Validate beam search parameters
        if self.num_beams <= 0:
            logger.warning(
                f"num_beams ({self.num_beams}) must be positive. Using default 4."
            )
            self.num_beams = 4
        
        if self.length_penalty < 0:
            logger.warning(
                f"length_penalty ({self.length_penalty}) should be non-negative. "
                f"Using default 2.0."
            )
            self.length_penalty = 2.0
        
        # Validate transcript and chunking parameters
        if self.max_transcript_chars <= 0:
            logger.warning(
                f"max_transcript_chars ({self.max_transcript_chars}) must be positive. "
                f"Using default 50000."
            )
            self.max_transcript_chars = 50000
        
        if self.chunk_max_tokens <= 0:
            logger.warning(
                f"chunk_max_tokens ({self.chunk_max_tokens}) must be positive. "
                f"Using default 1024."
            )
            self.chunk_max_tokens = 1024
        
        if self.chunk_overlap_tokens < 0:
            logger.warning(
                f"chunk_overlap_tokens ({self.chunk_overlap_tokens}) must be non-negative. "
                f"Using default 128."
            )
            self.chunk_overlap_tokens = 128
        
        if self.chunk_overlap_tokens >= self.chunk_max_tokens:
            logger.warning(
                f"chunk_overlap_tokens ({self.chunk_overlap_tokens}) must be less than "
                f"chunk_max_tokens ({self.chunk_max_tokens}). "
                f"Setting overlap to {self.chunk_max_tokens // 2}."
            )
            self.chunk_overlap_tokens = self.chunk_max_tokens // 2
        
        # Validate timeout (0 means no timeout)
        if self.inference_timeout < 0:
            logger.warning(
                f"inference_timeout ({self.inference_timeout}) must be non-negative. "
                f"Using default 0 (no timeout)."
            )
            self.inference_timeout = 0
        
        logger.info(
            f"BART configuration validated: device={self.device}, "
            f"max_length={self.max_length}, min_length={self.min_length}, "
            f"num_beams={self.num_beams}, enable_fallback={self.enable_fallback}, "
            f"inference_timeout={'no timeout' if self.inference_timeout == 0 else f'{self.inference_timeout}s'}"
        )
