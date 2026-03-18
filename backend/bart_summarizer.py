"""
BART summarizer module for meeting transcript summarization.

This module provides the core BART model loading and summarization functionality,
including lazy loading with caching, device management, and retry logic.
"""

import logging
import time
from functools import lru_cache
from typing import Tuple

import torch
from transformers import BartForConditionalGeneration, BartTokenizer

from bart_config import BARTConfig
from bart_exceptions import ModelLoadError

logger = logging.getLogger(__name__)

# Initialize config at module level
config = BARTConfig.from_env()
config.validate()


def _retry_with_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0
):
    """
    Retry function with exponential backoff.
    
    This function handles transient failures during model download by retrying
    with exponentially increasing delays between attempts.
    
    Args:
        func: Function to retry (should be a callable with no arguments)
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 2.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
    
    Returns:
        Result of successful function call
    
    Raises:
        Last exception if all retries fail
    
    Validates: Requirements 1.5, 6.5
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= backoff_factor
    
    # All retries exhausted
    raise last_exception


@lru_cache(maxsize=1)
def get_bart_model() -> Tuple[BartForConditionalGeneration, BartTokenizer]:
    """
    Lazy-load BART model and tokenizer with singleton pattern.
    
    This function uses @lru_cache to ensure the BART model is loaded exactly once
    and reused across all requests. It handles:
    - Model and tokenizer loading from Hugging Face
    - Device placement (CPU vs CUDA) based on configuration
    - Retry logic with exponential backoff for network failures
    - Proper error handling and logging
    
    The function follows the singleton pattern to minimize memory footprint and
    ensure consistent model state across requests.
    
    Returns:
        Tuple of (model, tokenizer):
            - model: BartForConditionalGeneration instance ready for inference
            - tokenizer: BartTokenizer instance for encoding/decoding
    
    Raises:
        ModelLoadError: If model loading fails after all retry attempts.
            This can occur due to:
            - Network errors during model download
            - Insufficient memory (RAM or VRAM)
            - Missing dependencies
            - Corrupted model files
            - Invalid cache directory
    
    Example:
        >>> model, tokenizer = get_bart_model()
        >>> inputs = tokenizer("Hello world", return_tensors="pt")
        >>> outputs = model.generate(**inputs)
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 6.5
    """
    try:
        model_name = "facebook/bart-large-cnn"
        
        logger.info(f"Loading BART model: {model_name}")
        logger.info(f"Target device: {config.device}")
        logger.info(f"Cache directory: {config.model_cache_dir or 'default (~/.cache/huggingface)'}")
        
        # Load tokenizer with retry logic
        logger.info("Loading tokenizer...")
        tokenizer = _retry_with_backoff(
            lambda: BartTokenizer.from_pretrained(
                model_name,
                cache_dir=config.model_cache_dir
            ),
            max_retries=3,
            initial_delay=2.0,
            backoff_factor=2.0
        )
        logger.info("Tokenizer loaded successfully")
        
        # Load model with retry logic
        logger.info("Loading model (this may take a few minutes on first run)...")
        model = _retry_with_backoff(
            lambda: BartForConditionalGeneration.from_pretrained(
                model_name,
                cache_dir=config.model_cache_dir
            ),
            max_retries=3,
            initial_delay=2.0,
            backoff_factor=2.0
        )
        logger.info("Model loaded successfully")
        
        # Handle device placement
        if config.device == "cuda":
            if torch.cuda.is_available():
                logger.info("CUDA is available, moving model to GPU")
                model = model.to("cuda")
                
                # Log GPU information
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                logger.info(f"Using GPU: {gpu_name} ({gpu_memory:.2f} GB)")
            else:
                logger.warning(
                    "CUDA device requested but not available. "
                    "Falling back to CPU. Install CUDA toolkit for GPU support."
                )
                model = model.to("cpu")
                config.device = "cpu"  # Update config to reflect actual device
        else:
            logger.info("Using CPU device")
            model = model.to("cpu")
        
        # Set model to evaluation mode (disables dropout, etc.)
        model.eval()
        
        logger.info(
            f"BART model initialization complete on {config.device} device"
        )
        
        return model, tokenizer
        
    except Exception as e:
        error_msg = f"Failed to load BART model after retries: {str(e)}"
        logger.error(error_msg)
        
        # Provide helpful error messages for common issues
        if "out of memory" in str(e).lower() or "oom" in str(e).lower():
            logger.error(
                "Insufficient memory to load model. "
                "Requirements: ~2GB RAM for CPU, ~4GB VRAM for GPU. "
                "Try closing other applications or using CPU mode."
            )
        elif "connection" in str(e).lower() or "network" in str(e).lower():
            logger.error(
                "Network error during model download. "
                "Check your internet connection and try again. "
                "If behind a proxy, configure HTTP_PROXY and HTTPS_PROXY environment variables."
            )
        elif "module" in str(e).lower() or "import" in str(e).lower():
            logger.error(
                "Missing dependencies. "
                "Ensure transformers, torch, and sentencepiece are installed: "
                "pip install transformers torch sentencepiece"
            )
        
        raise ModelLoadError(error_msg) from e


def _process_single_chunk(
    chunk: str,
    model: BartForConditionalGeneration,
    tokenizer: BartTokenizer,
    config: BARTConfig
) -> str:
    """
    Process a single transcript chunk through BART inference.
    
    This function handles the complete inference pipeline for a single chunk:
    - Tokenizes the input text with truncation and padding
    - Generates summary using beam search with configured parameters
    - Decodes output tokens back to human-readable text
    - Handles inference errors and timeouts
    
    Args:
        chunk: Text chunk to summarize (should be within token limits)
        model: BART model instance for inference
        tokenizer: BART tokenizer for encoding/decoding
        config: Configuration parameters for inference
    
    Returns:
        Generated summary text for the chunk
    
    Raises:
        InferenceError: If model inference fails
        InferenceTimeoutError: If inference exceeds timeout limit
    
    Example:
        >>> model, tokenizer = get_bart_model()
        >>> config = BARTConfig()
        >>> chunk = "This is a meeting transcript..."
        >>> summary = _process_single_chunk(chunk, model, tokenizer, config)
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.7
    """
    from bart_exceptions import InferenceError, InferenceTimeoutError
    import signal
    
    try:
        logger.debug(f"Processing chunk of length {len(chunk)} characters")
        
        # Tokenize input chunk with truncation and padding
        # truncation=True ensures we don't exceed model's max input length
        # padding=True ensures consistent tensor shapes
        # return_tensors="pt" returns PyTorch tensors
        inputs = tokenizer(
            chunk,
            return_tensors="pt",
            max_length=config.chunk_max_tokens,
            truncation=True,
            padding=True
        )
        
        # Move inputs to the appropriate device (CPU or CUDA)
        inputs = inputs.to(config.device)
        
        logger.debug(
            f"Tokenized chunk: {inputs['input_ids'].shape[1]} tokens"
        )
        
        # Set up timeout handler for inference (only if timeout > 0)
        timeout_supported = hasattr(signal, 'SIGALRM') and config.inference_timeout > 0
        old_handler = None
        
        if timeout_supported:
            def timeout_handler(signum, frame):
                raise InferenceTimeoutError(
                    f"Inference exceeded timeout of {config.inference_timeout} seconds"
                )
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(config.inference_timeout)
            logger.debug(f"Set inference timeout to {config.inference_timeout} seconds")
        else:
            logger.debug("No inference timeout set - BART will take as long as needed")
        
        try:
            # Generate summary using beam search
            # torch.no_grad() disables gradient computation for inference (saves memory)
            with torch.no_grad():
                outputs = model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_length=config.max_length,
                    min_length=config.min_length,
                    num_beams=config.num_beams,
                    length_penalty=config.length_penalty,
                    early_stopping=config.early_stopping,
                    no_repeat_ngram_size=config.no_repeat_ngram_size,
                    do_sample=config.do_sample
                )
            
            logger.debug(
                f"Generated output: {outputs.shape[1]} tokens"
            )
            
        finally:
            # Cancel timeout alarm if it was set
            if timeout_supported and old_handler is not None:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        # Decode output tokens to text
        # skip_special_tokens=True removes [CLS], [SEP], [PAD] tokens
        # outputs[0] gets the first (and only) sequence from the batch
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        logger.debug(f"Decoded summary: {len(summary)} characters")
        
        return summary
        
    except InferenceTimeoutError:
        # Re-raise timeout errors as-is
        logger.error(
            f"Inference timeout after {config.inference_timeout} seconds"
        )
        raise
        
    except Exception as e:
        # Wrap all other errors as InferenceError
        error_msg = f"BART inference failed: {str(e)}"
        logger.error(error_msg)
        
        # Provide helpful error messages for common issues
        if "out of memory" in str(e).lower() or "oom" in str(e).lower():
            logger.error(
                "GPU out of memory during inference. "
                "Try reducing chunk size or using CPU mode. "
                "Current chunk: ~{} tokens".format(
                    len(chunk.split())  # Rough token estimate
                )
            )
        elif "cuda" in str(e).lower() and config.device == "cuda":
            logger.error(
                "CUDA error during inference. "
                "Verify GPU is available and CUDA is properly installed. "
                "Consider falling back to CPU mode."
            )
        
        raise InferenceError(error_msg) from e


def _merge_chunk_summaries(
    summaries: list[str],
    tokenizer: BartTokenizer,
    config: BARTConfig
) -> str:
    """
    Merge multiple chunk summaries into coherent final summary.
    
    Algorithm:
    1. Split each summary into sentences
    2. Deduplicate sentences (case-insensitive comparison)
    3. Concatenate unique sentences
    4. If result exceeds max_length tokens, truncate at sentence boundary
    5. Ensure grammatical completeness
    
    Args:
        summaries: List of chunk summaries to merge
        tokenizer: BART tokenizer for token counting
        config: Configuration with max_length parameter
    
    Returns:
        Merged summary text
    
    Validates: Requirements 3.6, 12.4
    """
    import re
    
    all_sentences = []
    seen_sentences = set()
    
    # Extract and deduplicate sentences
    for summary in summaries:
        sentences = re.split(r'(?<=[.!?])\s+', summary.strip())
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Normalize for comparison (lowercase, remove extra spaces)
            normalized = ' '.join(sentence.lower().split())
            
            if normalized not in seen_sentences:
                seen_sentences.add(normalized)
                all_sentences.append(sentence)
    
    # Concatenate sentences
    merged = ' '.join(all_sentences)
    
    # Truncate if needed (at sentence boundary)
    tokens = tokenizer.encode(merged, add_special_tokens=False)
    if len(tokens) > config.max_length:
        # Find sentence boundary near max_length
        truncated_sentences = []
        token_count = 0
        
        for sentence in all_sentences:
            sentence_tokens = tokenizer.encode(sentence, add_special_tokens=False)
            sentence_token_count = len(sentence_tokens)
            if token_count + sentence_token_count <= config.max_length:
                truncated_sentences.append(sentence)
                token_count += sentence_token_count
            else:
                break
        
        merged = ' '.join(truncated_sentences)
    
    return merged


def generate_bart_summary(transcript: str, bart_config: BARTConfig, fallback_handler=None) -> str:
    """
    Generate summary using BART model with meeting-specific enhancements.
    
    This is the main entry point for BART summarization. It wraps the complete
    summarization pipeline with error handling and fallback logic:
    
    1. Preprocess transcript (normalize, validate, chunk if needed)
    2. Load BART model (lazy-loaded, cached)
    3. Process each chunk through BART inference
    4. Merge chunk summaries into final summary
    5. Apply meeting-specific post-processing for better results
    6. On any error, use fallback if enabled
    7. Log all fallback activations with error details
    
    Args:
        transcript: Raw meeting transcript text
        bart_config: BARTConfig instance with model parameters
        fallback_handler: Optional FallbackHandler instance for metrics tracking
    
    Returns:
        Generated summary text or fallback summary on error
    
    Raises:
        Exception: If error occurs and fallback is disabled (BART_ENABLE_FALLBACK=false)
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.3, 6.4, 6.6
    """
    from bart_preprocessor import preprocess_transcript
    from bart_exceptions import BARTError
    from meeting_analysis import extract_summary
    from meeting_summarizer import generate_meeting_summary
    
    try:
        logger.info("Starting BART summarization with meeting enhancements")
        
        # Load model and tokenizer
        model, tokenizer = get_bart_model()
        
        # Preprocess transcript
        logger.info("Preprocessing transcript")
        chunks = preprocess_transcript(transcript, tokenizer, bart_config)
        
        logger.info(f"Processing {len(chunks)} chunk(s)")
        
        # Process each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            logger.debug(f"Processing chunk {i}/{len(chunks)}")
            summary = _process_single_chunk(chunk, model, tokenizer, bart_config)
            chunk_summaries.append(summary)
        
        # Merge summaries if multiple chunks
        if len(chunk_summaries) == 1:
            bart_summary = chunk_summaries[0]
        else:
            logger.info(f"Merging {len(chunk_summaries)} chunk summaries")
            bart_summary = _merge_chunk_summaries(chunk_summaries, tokenizer, bart_config)
        
        # Apply meeting-specific enhancements
        logger.info("Applying meeting-specific enhancements")
        final_summary = generate_meeting_summary(transcript, bart_summary)
        
        logger.info("BART summarization with enhancements completed successfully")
        if fallback_handler:
            fallback_handler.record_bart_request()
        return final_summary
        
    except BARTError as e:
        # Handle BART-specific errors
        logger.error(f"BART error during summarization: {e}")
        
        if not bart_config.enable_fallback:
            logger.error("Fallback disabled, re-raising error")
            raise
        
        # Use fallback summarization
        logger.info("Activating fallback summarization")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        return extract_summary(transcript)
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during BART summarization: {e}")
        
        if not bart_config.enable_fallback:
            logger.error("Fallback disabled, re-raising error")
            raise
        
        # Use fallback summarization
        logger.info("Activating fallback summarization due to unexpected error")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        return extract_summary(transcript)
