"""
NVIDIA Qwen 3.5 summarizer module for meeting transcript summarization.

This module provides NVIDIA Qwen 3.5 integration for high-quality 
meeting summarization with proper error handling, retry logic, and fallback mechanisms.
"""

import json
import logging
import time
from typing import Optional, Dict, List

import requests

from nvidia_config import NVIDIAConfig

logger = logging.getLogger(__name__)

# Initialize config at module level
config = NVIDIAConfig.from_env()
config.validate()

# Global storage for parsed meeting data
_parsed_meeting_data = {
    "summary": "",
    "decisions": [],
    "action_items": []
}


def _create_meeting_prompt(transcript: str) -> str:
    """
    Create a structured prompt for NVIDIA Qwen 3.5 meeting analysis.
    
    Args:
        transcript: Meeting transcript text
    
    Returns:
        Formatted prompt for NVIDIA Qwen 3.5
    """
    prompt = f"""Analyze this meeting transcript and return JSON only.

Format:
{{
  "summary": "Brief summary (2-3 sentences)",
  "decisions": ["Decision 1", "Decision 2"],
  "action_items": [
    {{
      "task": "Task description",
      "owner": "Person or 'Not specified'",
      "deadline": "Deadline or 'Not specified'"
    }}
  ]
}}

Transcript: {transcript}"""
    
    return prompt


def _parse_json_response(response_text: str) -> Dict:
    """
    Parse JSON response from NVIDIA Qwen 3.5.
    
    Args:
        response_text: Raw response from NVIDIA API
    
    Returns:
        Parsed JSON data or fallback structure
    """
    try:
        # Try to parse as JSON directly
        parsed = json.loads(response_text.strip())
        
        # Validate required fields
        if not isinstance(parsed, dict):
            raise ValueError("Response is not a JSON object")
        
        # Ensure required fields exist with defaults
        result = {
            "summary": parsed.get("summary", ""),
            "decisions": parsed.get("decisions", []),
            "action_items": parsed.get("action_items", [])
        }
        
        # Validate action items structure
        if isinstance(result["action_items"], list):
            validated_actions = []
            for item in result["action_items"]:
                if isinstance(item, dict):
                    validated_actions.append({
                        "task": item.get("task", ""),
                        "owner": item.get("owner", "Not specified"),
                        "deadline": item.get("deadline", "Not specified")
                    })
                elif isinstance(item, str):
                    # Convert string to structured format
                    validated_actions.append({
                        "task": item,
                        "owner": "Not specified",
                        "deadline": "Not specified"
                    })
            result["action_items"] = validated_actions
        
        logger.info(f"Successfully parsed JSON response: {len(result['decisions'])} decisions, {len(result['action_items'])} action items")
        return result
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON response: {e}")
        # Try to extract content between braces
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_part = response_text[start:end]
                return json.loads(json_part)
        except:
            pass
        
        # Fallback: return response as summary
        return {
            "summary": response_text.strip(),
            "decisions": [],
            "action_items": []
        }
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        return {
            "summary": response_text.strip(),
            "decisions": [],
            "action_items": []
        }


def _retry_with_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0
):
    """
    Retry function with exponential backoff for API calls.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
    
    Returns:
        Result of successful function call
    
    Raises:
        Last exception if all retries fail
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


def get_nvidia_decisions() -> List[str]:
    """Get decisions extracted by NVIDIA Qwen 3.5."""
    return _parsed_meeting_data.get("decisions", [])


def get_nvidia_action_items() -> List[Dict]:
    """Get action items extracted by NVIDIA Qwen 3.5."""
    return _parsed_meeting_data.get("action_items", [])


def generate_nvidia_summary(transcript: str, nvidia_config: NVIDIAConfig, fallback_handler=None) -> str:
    """
    Generate summary using NVIDIA Qwen 3.5 with retry logic and error handling.
    
    Args:
        transcript: Meeting transcript text
        nvidia_config: NVIDIAConfig instance with parameters
        fallback_handler: Optional fallback handler for error tracking
    
    Returns:
        Generated summary text or fallback summary on error
    
    Raises:
        Exception: If error occurs and fallback is disabled
    """
    global _parsed_meeting_data
    
    try:
        logger.info("Starting NVIDIA Qwen 3.5 summarization")
        
        # Validate transcript length
        if len(transcript) > nvidia_config.max_transcript_chars:
            logger.warning(
                f"Transcript length ({len(transcript)}) exceeds maximum "
                f"({nvidia_config.max_transcript_chars}). Truncating."
            )
            transcript = transcript[:nvidia_config.max_transcript_chars]
        
        # Create prompt
        prompt = _create_meeting_prompt(transcript)
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {nvidia_config.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Prepare request payload
        payload = {
            "model": nvidia_config.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": nvidia_config.max_tokens,
            "temperature": nvidia_config.temperature,
            "top_p": nvidia_config.top_p,
            "top_k": nvidia_config.top_k,
            "presence_penalty": nvidia_config.presence_penalty,
            "repetition_penalty": nvidia_config.repetition_penalty,
            "stream": False,
            "chat_template_kwargs": {
                "enable_thinking": nvidia_config.enable_thinking
            }
        }
        
        # Make API call with retry logic
        def make_api_call():
            # Set timeout to None if request_timeout is 0 (no timeout)
            timeout = nvidia_config.request_timeout if nvidia_config.request_timeout > 0 else None
            
            response = requests.post(
                nvidia_config.base_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if "choices" not in result or not result["choices"]:
                raise ValueError(f"Invalid response from NVIDIA API: {result}")
            
            return result["choices"][0]["message"]["content"].strip()
        
        raw_response = _retry_with_backoff(
            make_api_call,
            max_retries=nvidia_config.max_retries,
            initial_delay=2.0,
            backoff_factor=2.0
        )
        
        # Parse JSON response
        parsed_data = _parse_json_response(raw_response)
        
        # Store globally for other endpoints
        _parsed_meeting_data = parsed_data
        
        # Return only the summary
        summary = parsed_data.get("summary", "No summary available.")
        
        logger.info("NVIDIA Qwen 3.5 summarization completed successfully")
        if fallback_handler:
            fallback_handler.record_nvidia_request()
        
        return summary
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error with NVIDIA API: {e}")
        if not nvidia_config.enable_fallback:
            raise
        
        logger.info("Activating fallback summarization due to HTTP error")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        
        # Reset parsed data
        _parsed_meeting_data = {"summary": "", "decisions": [], "action_items": []}
        from meeting_analysis import extract_summary
        return extract_summary(transcript)
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error with NVIDIA API: {e}")
        if not nvidia_config.enable_fallback:
            raise
        
        logger.info("Activating fallback summarization due to timeout")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        
        # Reset parsed data
        _parsed_meeting_data = {"summary": "", "decisions": [], "action_items": []}
        from meeting_analysis import extract_summary
        return extract_summary(transcript)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error with NVIDIA API: {e}")
        if not nvidia_config.enable_fallback:
            raise
        
        logger.info("Activating fallback summarization due to request error")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        
        # Reset parsed data
        _parsed_meeting_data = {"summary": "", "decisions": [], "action_items": []}
        from meeting_analysis import extract_summary
        return extract_summary(transcript)
        
    except Exception as e:
        logger.error(f"Unexpected error during NVIDIA Qwen 3.5 summarization: {e}")
        if not nvidia_config.enable_fallback:
            raise
        
        logger.info("Activating fallback summarization due to unexpected error")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        
        # Reset parsed data
        _parsed_meeting_data = {"summary": "", "decisions": [], "action_items": []}
        from meeting_analysis import extract_summary
        return extract_summary(transcript)