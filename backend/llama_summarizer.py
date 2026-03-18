"""
LLaMA 3 summarizer module for meeting transcript summarization.

This module provides LLaMA 3 integration via Ollama for high-quality local 
meeting summarization with proper error handling, retry logic, and fallback mechanisms.
"""

import json
import logging
import time
from typing import Optional, Dict, List

import requests

from llama_config import LLaMAConfig

logger = logging.getLogger(__name__)

# Initialize config at module level
config = LLaMAConfig.from_env()
config.validate()

# Global storage for parsed meeting data
_parsed_meeting_data = {
    "summary": "",
    "decisions": [],
    "action_items": []
}


def _parse_json_response(response_text: str) -> Dict:
    """
    Parse JSON response from LLaMA 3.
    
    Args:
        response_text: Raw response from LLaMA 3
    
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


def get_llama_decisions() -> List[str]:
    """Get decisions extracted by LLaMA 3."""
    return _parsed_meeting_data.get("decisions", [])


def get_llama_action_items() -> List[Dict]:
    """Get action items extracted by LLaMA 3."""
    return _parsed_meeting_data.get("action_items", [])


def _create_meeting_prompt(transcript: str) -> str:
    """
    Create a structured prompt for LLaMA 3 meeting analysis.
    
    Args:
        transcript: Meeting transcript text
    
    Returns:
        Formatted prompt for LLaMA 3
    """
    prompt = f"""You are an AI Meeting Assistant.Your task is to analyze a meeting transcript and extract structured information.IMPORTANT RULES:- Return ONLY valid JSON (no extra text, no explanation)- Do NOT include markdown formatting- Do NOT repeat labels inside fields- Keep responses concise and professional- If something is not present, return an empty list []OUTPUT FORMAT:{{"summary": "Short clear paragraph (3-5 lines max)","decisions": ["Decision 1","Decision 2"],"action_items": [{{"task": "What needs to be done","owner": "Person responsible (or 'Not specified')","deadline": "Deadline if mentioned (or 'Not specified')"}}]}}INSTRUCTIONS:1. Summary → High-level overview of discussion2. Decisions → Only confirmed decisions (NOT suggestions)3. Action Items → Only tasks that require follow-up4. Extract owner and deadline ONLY if explicitly mentioned5. Do NOT hallucinate names, deadlines, or decisionsTRANSCRIPT:{transcript}"""
    
    return prompt


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


def check_ollama_status(llama_config: LLaMAConfig) -> bool:
    """
    Check if Ollama server is running and the model is available.
    
    Args:
        llama_config: LLaMA configuration
    
    Returns:
        True if Ollama is available, False otherwise
    """
    try:
        # Check if Ollama server is running
        response = requests.get(f"{llama_config.base_url}/api/tags", timeout=5)
        if response.status_code != 200:
            logger.error(f"Ollama server not responding: {response.status_code}")
            return False
        
        # Check if the model is available
        models = response.json().get("models", [])
        model_names = [model.get("name", "") for model in models]
        
        # Check for exact match or partial match (e.g., "llama3" matches "llama3:latest")
        model_available = any(
            llama_config.model in model_name or model_name.startswith(llama_config.model + ":")
            for model_name in model_names
        )
        
        if not model_available:
            logger.error(
                f"Model '{llama_config.model}' not found. Available models: {model_names}"
            )
            return False
        
        logger.info(f"Ollama server is running with model '{llama_config.model}'")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Ollama server: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking Ollama status: {e}")
        return False


def generate_llama_summary(transcript: str, llama_config: LLaMAConfig, fallback_handler=None) -> str:
    """
    Generate summary using LLaMA 3 with retry logic and error handling.
    
    Args:
        transcript: Meeting transcript text
        llama_config: LLaMAConfig instance with parameters
        fallback_handler: Optional fallback handler for error tracking
    
    Returns:
        Generated summary text or fallback summary on error
    
    Raises:
        Exception: If error occurs and fallback is disabled
    """
    global _parsed_meeting_data
    
    try:
        logger.info("Starting LLaMA 3 summarization")
        
        # Check if Ollama is available
        if not check_ollama_status(llama_config):
            raise ConnectionError("Ollama server is not available or model is not loaded")
        
        # Validate transcript length
        if len(transcript) > llama_config.max_transcript_chars:
            logger.warning(
                f"Transcript length ({len(transcript)}) exceeds maximum "
                f"({llama_config.max_transcript_chars}). Truncating."
            )
            transcript = transcript[:llama_config.max_transcript_chars]
        
        # Create prompt
        prompt = _create_meeting_prompt(transcript)
        
        # Prepare request payload
        payload = {
            "model": llama_config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": llama_config.temperature,
                "num_predict": llama_config.max_tokens,
            }
        }
        
        # Make API call with retry logic
        def make_api_call():
            response = requests.post(
                f"{llama_config.base_url}/api/generate",
                json=payload,
                timeout=llama_config.request_timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if "response" not in result:
                raise ValueError(f"Invalid response from Ollama: {result}")
            
            return result["response"].strip()
        
        raw_response = _retry_with_backoff(
            make_api_call,
            max_retries=llama_config.max_retries,
            initial_delay=2.0,
            backoff_factor=2.0
        )
        
        # Parse JSON response
        parsed_data = _parse_json_response(raw_response)
        
        # Store globally for other endpoints
        _parsed_meeting_data = parsed_data
        
        # Return only the summary
        summary = parsed_data.get("summary", "No summary available.")
        
        logger.info("LLaMA 3 summarization completed successfully")
        if fallback_handler:
            fallback_handler.record_llama_request()
        
        return summary
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error to Ollama server: {e}")
        if not llama_config.enable_fallback:
            raise
        
        logger.info("Activating fallback summarization due to connection error")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        
        # Reset parsed data
        _parsed_meeting_data = {"summary": "", "decisions": [], "action_items": []}
        from meeting_analysis import extract_summary
        return extract_summary(transcript)
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error with Ollama server: {e}")
        if not llama_config.enable_fallback:
            raise
        
        logger.info("Activating fallback summarization due to timeout")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        
        # Reset parsed data
        _parsed_meeting_data = {"summary": "", "decisions": [], "action_items": []}
        from meeting_analysis import extract_summary
        return extract_summary(transcript)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error with Ollama server: {e}")
        if not llama_config.enable_fallback:
            raise
        
        logger.info("Activating fallback summarization due to request error")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        
        # Reset parsed data
        _parsed_meeting_data = {"summary": "", "decisions": [], "action_items": []}
        from meeting_analysis import extract_summary
        return extract_summary(transcript)
        
    except Exception as e:
        logger.error(f"Unexpected error during LLaMA 3 summarization: {e}")
        if not llama_config.enable_fallback:
            raise
        
        logger.info("Activating fallback summarization due to unexpected error")
        if fallback_handler:
            fallback_handler.record_fallback_request()
        
        # Reset parsed data
        _parsed_meeting_data = {"summary": "", "decisions": [], "action_items": []}
        from meeting_analysis import extract_summary
        return extract_summary(transcript)