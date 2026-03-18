"""
Transcript preprocessing module for BART-large-CNN integration.

This module provides functions to prepare meeting transcripts for BART model input,
including text normalization, validation, and chunking with sentence-boundary preservation.
"""

import logging
import re
from typing import List, Tuple, TYPE_CHECKING

from transformers import BartTokenizer

from bart_exceptions import PreprocessingError, TranscriptTooLongError

if TYPE_CHECKING:
    from bart_config import BARTConfig

logger = logging.getLogger(__name__)


def _add_summarization_instruction(text: str, config: 'BARTConfig') -> str:
    """
    Prepare text for BART summarization.
    
    For BART-large-cnn, we don't add instruction prefixes as it's not an 
    instruction-following model. Instead, we return the text as-is and let
    BART's natural summarization training handle it.
    
    Args:
        text: Normalized transcript text
        config: BART configuration containing prompt settings
    
    Returns:
        Text prepared for BART summarization (usually unchanged)
    """
    if config.custom_prompt:
        # Only use custom prompt if explicitly provided
        return config.custom_prompt + " " + text
    else:
        # For best results with BART-large-cnn, use the text as-is
        return text


def _normalize_text(text: str) -> str:
    """
    Normalize whitespace and line endings in transcript text.
    
    This function:
    - Replaces multiple consecutive spaces with a single space
    - Replaces multiple consecutive newlines with a single newline
    - Removes leading and trailing whitespace
    - Normalizes line endings to Unix-style (\n)
    
    Args:
        text: Raw transcript text with potentially excessive whitespace
    
    Returns:
        Normalized text with cleaned whitespace
    
    Validates: Requirements 2.6
    """
    if not text:
        return ""
    
    # Normalize line endings to Unix-style
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Replace multiple consecutive spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple consecutive newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Remove leading and trailing whitespace
    text = text.strip()
    
    return text


def validate_transcript(transcript: str, max_chars: int = 50000) -> Tuple[bool, str]:
    """
    Validate transcript meets requirements.
    
    Checks:
    - Transcript is not empty or only whitespace
    - Transcript does not exceed maximum character limit
    
    Args:
        transcript: Raw transcript text to validate
        max_chars: Maximum allowed character count (default: 50000)
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if transcript is valid, False otherwise
        - error_message: Empty string if valid, error description if invalid
    
    Validates: Requirements 2.7, 6.7
    """
    # Check for empty or whitespace-only transcript
    if not transcript or not transcript.strip():
        return False, "Transcript is empty or contains only whitespace"
    
    # Check for excessive length
    if len(transcript) > max_chars:
        return False, f"Transcript exceeds maximum length of {max_chars} characters (got {len(transcript)})"
    
    return True, ""


def _chunk_by_sentences(
    text: str,
    tokenizer: BartTokenizer,
    max_length: int = 1024,
    overlap: int = 128
) -> List[str]:
    """
    Split text into overlapping chunks at sentence boundaries.
    
    Algorithm:
    1. Split text into sentences using regex pattern
    2. Tokenize each sentence to count tokens
    3. Build chunks by accumulating sentences until near max_length
    4. Add overlap_tokens from end of previous chunk to start of next chunk
    5. Ensure no chunk exceeds max_length tokens
    
    This preserves sentence boundaries (never splits mid-sentence) and maintains
    context through overlap between consecutive chunks.
    
    Args:
        text: Normalized transcript text
        tokenizer: BART tokenizer instance
        max_length: Maximum tokens per chunk (default: 1024)
        overlap: Token overlap between chunks for context preservation (default: 128)
    
    Returns:
        List of text chunks, each within token limit and preserving sentence boundaries
    
    Validates: Requirements 2.3, 2.4, 2.5
    """
    # Split into sentences using regex pattern (split after .!? followed by whitespace)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Handle edge case: empty text
    if not sentences or (len(sentences) == 1 and not sentences[0].strip()):
        return []
    
    # Tokenize each sentence and store with original text
    sentence_data = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        tokens = tokenizer.encode(sentence, add_special_tokens=False)
        sentence_data.append((sentence, tokens, len(tokens)))
    
    # Handle edge case: no valid sentences
    if not sentence_data:
        return []
    
    # Build chunks
    chunks = []
    current_chunk_sentences = []
    current_token_count = 0
    
    for i, (sentence, tokens, token_count) in enumerate(sentence_data):
        # Check if adding this sentence would exceed limit
        if current_token_count + token_count > max_length and current_chunk_sentences:
            # Save current chunk
            chunk_text = ' '.join(current_chunk_sentences)
            chunks.append(chunk_text)
            
            # Calculate overlap for next chunk
            # Take sentences from end of current chunk until we reach overlap limit
            overlap_sentences = []
            overlap_token_count = 0
            
            for j in range(len(current_chunk_sentences) - 1, -1, -1):
                sent = current_chunk_sentences[j]
                sent_tokens = tokenizer.encode(sent, add_special_tokens=False)
                sent_token_count = len(sent_tokens)
                
                if overlap_token_count + sent_token_count <= overlap:
                    overlap_sentences.insert(0, sent)
                    overlap_token_count += sent_token_count
                else:
                    break
            
            # Start new chunk with overlap + current sentence
            current_chunk_sentences = overlap_sentences + [sentence]
            current_token_count = overlap_token_count + token_count
        else:
            # Add sentence to current chunk
            current_chunk_sentences.append(sentence)
            current_token_count += token_count
    
    # Add final chunk if it has content
    if current_chunk_sentences:
        chunk_text = ' '.join(current_chunk_sentences)
        chunks.append(chunk_text)
    
    return chunks


def preprocess_transcript(
    transcript: str,
    tokenizer: BartTokenizer,
    config: 'BARTConfig'
) -> List[str]:
    """
    Preprocess transcript into BART-ready chunks.
    
    This is the main preprocessing function that orchestrates:
    1. Text normalization (whitespace cleanup)
    2. Transcript validation (length and content checks)
    3. Chunking (if needed) with sentence-boundary preservation
    
    Args:
        transcript: Raw transcript text
        tokenizer: BART tokenizer instance
        config: BART configuration with max_length and overlap settings
    
    Returns:
        List of text chunks, each within token limit
        - Single-element list for short transcripts
        - Multiple elements for long transcripts requiring chunking
    
    Raises:
        TranscriptTooLongError: If transcript exceeds maximum character limit
        PreprocessingError: If transcript validation fails or preprocessing encounters errors
    
    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8
    """
    try:
        # Step 1: Normalize text
        normalized_text = _normalize_text(transcript)
        
        # Step 1.5: Add summarization instruction to guide BART
        instructed_text = _add_summarization_instruction(normalized_text, config)
        
        # Step 2: Validate transcript (use original normalized text for validation)
        is_valid, error_message = validate_transcript(
            normalized_text,  # Validate original text, not instructed version
            max_chars=config.max_transcript_chars
        )
        
        if not is_valid:
            if "exceeds maximum length" in error_message:
                raise TranscriptTooLongError(error_message)
            else:
                raise PreprocessingError(error_message)
        
        # Step 3: Tokenize instructed text to check if chunking is needed
        tokens = tokenizer.encode(instructed_text, add_special_tokens=False)
        token_count = len(tokens)
        
        logger.info(f"Transcript has {token_count} tokens")
        
        # Step 4: Chunk if needed, otherwise return as single chunk
        if token_count <= config.chunk_max_tokens:
            # Short transcript - no chunking needed
            logger.info("Transcript fits in single chunk")
            return [instructed_text]
        else:
            # Long transcript - apply chunking strategy
            logger.info(f"Transcript exceeds {config.chunk_max_tokens} tokens, applying chunking")
            chunks = _chunk_by_sentences(
                instructed_text,  # Use instructed text for chunking
                tokenizer,
                max_length=config.chunk_max_tokens,
                overlap=config.chunk_overlap_tokens
            )
            
            logger.info(f"Split transcript into {len(chunks)} chunks")
            
            # Validate chunks
            if not chunks:
                raise PreprocessingError("Chunking produced no valid chunks")
            
            return chunks
            
    except (TranscriptTooLongError, PreprocessingError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Wrap unexpected errors
        logger.error(f"Unexpected error during preprocessing: {e}")
        raise PreprocessingError(f"Preprocessing failed: {str(e)}") from e
