"""
Internal data models for BART summarization.

This module defines dataclasses for internal data structures used
in the BART summarization pipeline.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SummarizationRequest:
    """
    Internal request model for summarization.
    
    Attributes:
        transcript: Raw meeting transcript text to summarize
        max_length: Maximum summary length in tokens (default: 150)
        min_length: Minimum summary length in tokens (default: 40)
        num_beams: Beam search width for generation (default: 4)
    
    Validates: Requirements 3.1, 3.2, 3.3
    """
    transcript: str
    max_length: int = 150
    min_length: int = 40
    num_beams: int = 4


@dataclass
class SummarizationResult:
    """
    Internal result model for summarization.
    
    Attributes:
        summary: Generated summary text
        source: Source of summary ("bart" or "fallback")
        processing_time: Time taken to generate summary in seconds
        chunk_count: Number of chunks processed (1 for short transcripts)
        error: Error message if summarization failed (None on success)
    
    Validates: Requirements 3.1, 3.2, 3.3
    """
    summary: str
    source: str  # "bart" or "fallback"
    processing_time: float
    chunk_count: int
    error: Optional[str] = None


@dataclass
class ChunkMetadata:
    """
    Metadata for transcript chunks.
    
    Attributes:
        chunk_index: Index of this chunk (0-based)
        total_chunks: Total number of chunks in transcript
        token_count: Number of tokens in this chunk
        char_count: Number of characters in this chunk
        has_overlap: Whether this chunk has overlap with previous chunk
    
    Validates: Requirements 3.1, 3.2, 3.3
    """
    chunk_index: int
    total_chunks: int
    token_count: int
    char_count: int
    has_overlap: bool
