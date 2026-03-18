"""
Fallback handler for LLaMA 3 summarization errors.

This module provides error tracking and fallback logic when LLaMA 3 API calls fail.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class LLaMAFallbackHandler:
    """
    Handles LLaMA 3 errors and provides fallback summarization.
    
    This class tracks LLaMA 3 API errors and provides metrics for monitoring
    the health of the LLaMA 3 integration.
    """
    
    def __init__(self):
        self.llama_requests = 0
        self.fallback_requests = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.last_error_time: Optional[datetime] = None
        self.llama_available = True
    
    def record_llama_request(self):
        """Record a successful LLaMA 3 request."""
        self.llama_requests += 1
        self.llama_available = True
    
    def record_fallback_request(self):
        """Record a fallback request due to LLaMA 3 failure."""
        self.fallback_requests += 1
        self.error_count += 1
    
    def handle_error(self, error: Exception, transcript: str) -> str:
        """
        Handle LLaMA 3 error and return fallback summary.
        
        Args:
            error: The exception that occurred
            transcript: Original transcript text
        
        Returns:
            Fallback summary from regex-based extraction
        """
        self.error_count += 1
        self.last_error = str(error)
        self.last_error_time = datetime.now()
        
        # Mark LLaMA 3 as potentially unavailable after multiple errors
        if self.error_count >= 5:
            self.llama_available = False
            logger.warning(
                f"LLaMA 3 marked as unavailable after {self.error_count} errors. "
                f"Last error: {self.last_error}"
            )
        
        logger.info(f"Using fallback summarization due to error: {error}")
        
        # Use existing regex-based summarization as fallback
        from meeting_analysis import extract_summary
        return extract_summary(transcript)
    
    def mark_llama_unavailable(self):
        """Mark LLaMA 3 as unavailable for all subsequent requests."""
        self.llama_available = False
        logger.warning("LLaMA 3 manually marked as unavailable")
    
    def is_llama_available(self) -> bool:
        """Check if LLaMA 3 is available for requests."""
        return self.llama_available
    
    def get_status(self) -> dict:
        """
        Get current status and metrics.
        
        Returns:
            Dictionary with status information:
            - llama_available: Whether LLaMA 3 is available
            - total_requests: Total summarization requests
            - llama_requests: Successful LLaMA 3 requests
            - fallback_requests: Fallback requests
            - error_count: Total errors
            - fallback_rate: Percentage of requests using fallback
            - last_error: Last error message
            - last_error_time: When last error occurred
        """
        total_requests = self.llama_requests + self.fallback_requests
        fallback_rate = (
            (self.fallback_requests / total_requests * 100) 
            if total_requests > 0 else 0
        )
        
        return {
            "llama_available": self.llama_available,
            "total_requests": total_requests,
            "llama_requests": self.llama_requests,
            "fallback_requests": self.fallback_requests,
            "error_count": self.error_count,
            "fallback_rate": round(fallback_rate, 2),
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None
        }