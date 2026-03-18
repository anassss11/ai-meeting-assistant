"""
Exception hierarchy for BART-large-CNN integration.

This module defines custom exceptions for BART model operations,
providing granular error handling for different failure scenarios.
"""


class BARTError(Exception):
    """
    Base exception class for all BART-related errors.
    
    All BART-specific exceptions inherit from this base class,
    allowing for catch-all error handling when needed.
    """
    pass


class ModelLoadError(BARTError):
    """
    Exception raised when BART model fails to load.
    
    This can occur due to:
    - Missing model files
    - Insufficient memory
    - Network errors during model download
    - Incompatible model versions
    - Missing dependencies
    
    Validates: Requirements 6.1, 6.2
    """
    pass


class PreprocessingError(BARTError):
    """
    Exception raised when transcript preprocessing fails.
    
    This can occur due to:
    - Invalid input format
    - Tokenization failures
    - Chunking algorithm errors
    - Text normalization issues
    
    Validates: Requirements 6.3
    """
    pass


class InferenceError(BARTError):
    """
    Exception raised when BART model inference fails.
    
    This can occur due to:
    - Model execution errors
    - Invalid model output
    - CUDA errors during GPU inference
    - Memory errors during inference
    
    Validates: Requirements 6.3, 6.4
    """
    pass


class InferenceTimeoutError(InferenceError):
    """
    Exception raised when BART inference exceeds timeout limit.
    
    This occurs when model inference takes longer than the configured
    timeout period (default: 30 seconds). Inherits from InferenceError
    as it's a specific type of inference failure.
    
    Validates: Requirements 6.4
    """
    pass


class TranscriptTooLongError(BARTError):
    """
    Exception raised when transcript exceeds maximum allowed length.
    
    This occurs when the input transcript exceeds the configured
    maximum character limit (default: 50,000 characters), indicating
    the transcript is too large to process even with chunking.
    
    Validates: Requirements 6.7
    """
    pass


class InvalidConfigError(BARTError):
    """
    Exception raised when BART configuration is invalid.
    
    This can occur due to:
    - Invalid device specification (not 'cpu' or 'cuda')
    - Invalid parameter ranges (e.g., max_length < min_length)
    - Missing required configuration values
    - Incompatible configuration combinations
    
    Validates: Requirements 6.7
    """
    pass
