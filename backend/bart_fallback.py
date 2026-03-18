"""
Fallback handler for BART model errors.

This module provides graceful degradation to regex-based summarization
when BART model is unavailable or encounters errors during inference.
"""

import logging
from typing import Optional

from bart_config import BARTConfig

logger = logging.getLogger(__name__)


class FallbackHandler:
    """
    Manages fallback to regex-based summarization when BART fails.
    
    This handler tracks BART availability and error state, providing
    graceful degradation to regex-based summarization when needed.
    
    Validates: Requirements 6.1, 6.2, 6.3, 6.6, 6.8
    """
    
    def __init__(self, config: BARTConfig):
        """
        Initialize the fallback handler.
        
        Args:
            config: BARTConfig instance with fallback settings
        """
        self.config = config
        self.bart_available = True
        self.error_count = 0
        self.last_error: Optional[Exception] = None
        
        # Metrics tracking
        self.total_requests = 0
        self.bart_requests = 0
        self.fallback_requests = 0
    
    def handle_error(self, error: Exception, transcript: str) -> str:
        """
        Handle BART error and return fallback summary.
        
        Logs the error, increments error counter, and returns a fallback
        summary using regex-based extraction from meeting_analysis module.
        
        Args:
            error: Exception from BART processing
            transcript: Original transcript text
        
        Returns:
            Fallback summary from regex-based logic
        
        Raises:
            Exception: If fallback is disabled (BART_ENABLE_FALLBACK=false)
        
        Validates: Requirements 6.1, 6.2, 6.3
        """
        self.error_count += 1
        self.last_error = error
        
        logger.error(f"BART summarization failed: {error}")
        logger.info("Falling back to regex-based summarization")
        
        if not self.config.enable_fallback:
            logger.error("Fallback disabled, re-raising error")
            raise error
        
        # Import here to avoid circular dependency
        from meeting_analysis import extract_summary
        
        try:
            fallback_summary = extract_summary(transcript)
            logger.info("Fallback summarization completed successfully")
            return fallback_summary
        except Exception as fallback_error:
            logger.error(f"Fallback summarization also failed: {fallback_error}")
            raise fallback_error
    
    def mark_bart_unavailable(self) -> None:
        """
        Mark BART as unavailable for all subsequent requests.
        
        This is called when BART model fails to load at startup,
        ensuring all requests use fallback mode without attempting
        to load the model again.
        
        Validates: Requirements 6.1, 6.2
        """
        self.bart_available = False
        logger.warning("BART marked as unavailable, using fallback mode for all requests")
    
    def is_bart_available(self) -> bool:
        """
        Check if BART is currently available.
        
        Returns:
            True if BART is available, False if using fallback mode
        
        Validates: Requirements 6.6
        """
        return self.bart_available
    
    def get_status(self) -> dict[str, object]:
        """
        Return fallback handler status for monitoring.
        
        Returns a dictionary containing current status metrics including
        BART availability, error count, and last error information.
        
        Returns:
            Dictionary with keys:
            - bart_available: bool indicating BART availability
            - error_count: int count of errors encountered
            - last_error: str description of last error or None
        
        Validates: Requirements 6.6, 6.8
        """
        return {
            "bart_available": self.bart_available,
            "error_count": self.error_count,
            "last_error": str(self.last_error) if self.last_error else None,
        }
    
    def record_bart_request(self) -> None:
        """
        Record a successful BART summarization request.
        
        Increments total_requests and bart_requests counters.
        
        Validates: Requirements 6.6
        """
        self.total_requests += 1
        self.bart_requests += 1
    
    def record_fallback_request(self) -> None:
        """
        Record a fallback summarization request.
        
        Increments total_requests and fallback_requests counters.
        
        Validates: Requirements 6.6
        """
        self.total_requests += 1
        self.fallback_requests += 1
    
    def get_metrics(self) -> dict[str, object]:
        """
        Return summarization metrics for monitoring and observability.
        
        Returns a dictionary containing request counts and fallback rate.
        
        Returns:
            Dictionary with keys:
            - total_requests: int total number of summarization requests
            - bart_requests: int number of successful BART requests
            - fallback_requests: int number of fallback requests
            - error_count: int number of errors encountered
            - fallback_rate: float percentage of requests using fallback (0.0-1.0)
        
        Validates: Requirements 6.6
        """
        fallback_rate = 0.0
        if self.total_requests > 0:
            fallback_rate = self.fallback_requests / self.total_requests
        
        return {
            "total_requests": self.total_requests,
            "bart_requests": self.bart_requests,
            "fallback_requests": self.fallback_requests,
            "error_count": self.error_count,
            "fallback_rate": fallback_rate,
        }
