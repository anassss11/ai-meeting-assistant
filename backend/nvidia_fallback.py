"""
Fallback handler for NVIDIA Qwen 3.5 summarization errors.

This module provides error tracking and fallback logic when NVIDIA API calls fail.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class NVIDIAFallbackHandler:
    """
    Handles NVIDIA Qwen 3.5 errors and provides fallback summarization.
    
    This class tracks NVIDIA API errors and provides metrics for monitoring
    the health of the NVIDIA integration.
    """
    
    def __init__(self):
        self.nvidia_requests = 0
        self.fallback_requests = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.last_error_time: Optional[datetime] = None
        self.nvidia_available = True
    
    def record_nvidia_request(self):
        """Record a successful NVIDIA request."""
        self.nvidia_requests += 1
        self.nvidia_available = True
    
    def record_fallback_request(self):
        """Record a fallback request due to NVIDIA failure."""
        self.fallback_requests += 1
        self.error_count += 1
    
    def handle_error(self, error: Exception, transcript: str) -> str:
        """
        Handle NVIDIA error and return fallback summary.
        
        Args:
            error: The exception that occurred
            transcript: Original transcript text
        
        Returns:
            Fallback summary from regex-based extraction
        """
        self.error_count += 1
        self.last_error = str(error)
        self.last_error_time = datetime.now()
        
        # Mark NVIDIA as potentially unavailable after multiple errors
        if self.error_count >= 5:
            self.nvidia_available = False
            logger.warning(
                f"NVIDIA marked as unavailable after {self.error_count} errors. "
                f"Last error: {self.last_error}"
            )
        
        logger.info(f"Using fallback summarization due to error: {error}")
        
        # Use existing regex-based summarization as fallback
        from meeting_analysis import extract_summary
        return extract_summary(transcript)
    
    def mark_nvidia_unavailable(self):
        """Mark NVIDIA as unavailable for all subsequent requests."""
        self.nvidia_available = False
        logger.warning("NVIDIA manually marked as unavailable")
    
    def is_nvidia_available(self) -> bool:
        """Check if NVIDIA is available for requests."""
        return self.nvidia_available
    
    def get_status(self) -> dict:
        """
        Get current status and metrics.
        
        Returns:
            Dictionary with status information:
            - nvidia_available: Whether NVIDIA is available
            - total_requests: Total summarization requests
            - nvidia_requests: Successful NVIDIA requests
            - fallback_requests: Fallback requests
            - error_count: Total errors
            - fallback_rate: Percentage of requests using fallback
            - last_error: Last error message
            - last_error_time: When last error occurred
        """
        total_requests = self.nvidia_requests + self.fallback_requests
        fallback_rate = (
            (self.fallback_requests / total_requests * 100) 
            if total_requests > 0 else 0
        )
        
        return {
            "nvidia_available": self.nvidia_available,
            "total_requests": total_requests,
            "nvidia_requests": self.nvidia_requests,
            "fallback_requests": self.fallback_requests,
            "error_count": self.error_count,
            "fallback_rate": round(fallback_rate, 2),
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None
        }