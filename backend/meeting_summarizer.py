"""
Meeting-specific summarizer that combines BART with meeting intelligence.

This module provides a hybrid approach that uses BART for initial summarization
and then applies meeting-specific post-processing to create better summaries.
"""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


def extract_meeting_elements(text: str) -> dict:
    """
    Extract key meeting elements from transcript text.
    
    Args:
        text: Meeting transcript text
    
    Returns:
        Dictionary with extracted elements:
        - decisions: List of decisions made
        - action_items: List of action items
        - key_topics: List of main discussion topics
        - participants: List of mentioned participants
    """
    # Decision patterns
    decision_patterns = [
        r"(?:we|team|they)\s+(?:decided|agreed|approved|chose|selected|finalized)",
        r"let'?s (?:go with|stick with|use|implement)",
        r"the (?:decision|plan) is to",
        r"we'?ll (?:go ahead|proceed) with"
    ]
    
    # Action item patterns
    action_patterns = [
        r"(?:i|we|you|they)\s+(?:will|need to|have to|should)\s+([^.!?]+)",
        r"(?:follow up|check|confirm|send|review|prepare|update)\s+([^.!?]+)",
        r"action item:?\s*([^.!?]+)",
        r"todo:?\s*([^.!?]+)"
    ]
    
    # Topic extraction (nouns and key phrases)
    topic_patterns = [
        r"(?:about|regarding|concerning)\s+([^.!?,]+)",
        r"(?:the|this|that)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})",
        r"(?:project|system|feature|issue|problem)\s+([^.!?,]+)"
    ]
    
    decisions = []
    action_items = []
    key_topics = []
    
    # Extract decisions
    for pattern in decision_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Get the sentence containing the decision
            sentence_start = text.rfind('.', 0, match.start()) + 1
            sentence_end = text.find('.', match.end())
            if sentence_end == -1:
                sentence_end = len(text)
            decision = text[sentence_start:sentence_end].strip()
            if decision and len(decision) > 10:
                decisions.append(decision)
    
    # Extract action items
    for pattern in action_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            action = match.group(1) if match.groups() else match.group(0)
            if action and len(action.strip()) > 5:
                action_items.append(action.strip())
    
    # Extract key topics
    for pattern in topic_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            topic = match.group(1) if match.groups() else match.group(0)
            if topic and len(topic.strip()) > 3:
                key_topics.append(topic.strip())
    
    return {
        'decisions': list(set(decisions))[:3],  # Top 3 unique decisions
        'action_items': list(set(action_items))[:5],  # Top 5 unique action items
        'key_topics': list(set(key_topics))[:4],  # Top 4 unique topics
    }


def create_structured_summary(bart_summary: str, meeting_elements: dict, original_length: int) -> str:
    """
    Create a structured meeting summary combining BART output with extracted elements.
    
    Args:
        bart_summary: Summary from BART model
        meeting_elements: Extracted meeting elements
        original_length: Length of original transcript
    
    Returns:
        Improved structured summary
    """
    # If BART summary is too similar to original (>80% length), create our own
    if len(bart_summary) > original_length * 0.8:
        # BART didn't summarize well, create summary from elements
        summary_parts = []
        
        if meeting_elements['key_topics']:
            topics = ', '.join(meeting_elements['key_topics'][:3])
            summary_parts.append(f"The team discussed {topics}")
        
        if meeting_elements['decisions']:
            decision = meeting_elements['decisions'][0]
            summary_parts.append(f"Key decision: {decision}")
        
        if meeting_elements['action_items']:
            action_count = len(meeting_elements['action_items'])
            if action_count == 1:
                summary_parts.append(f"Action item: {meeting_elements['action_items'][0]}")
            else:
                summary_parts.append(f"{action_count} action items were identified")
        
        if not summary_parts:
            # Fallback: create a simple summary
            words = bart_summary.split()
            if len(words) > 20:
                summary_parts.append(' '.join(words[:20]) + '...')
            else:
                summary_parts.append(bart_summary)
        
        return '. '.join(summary_parts) + '.'
    
    else:
        # BART did summarize, enhance it with key elements
        enhanced_summary = bart_summary
        
        # Add key decisions if not already mentioned
        if meeting_elements['decisions']:
            decision_keywords = ['decided', 'agreed', 'approved', 'chose']
            if not any(keyword in enhanced_summary.lower() for keyword in decision_keywords):
                decision = meeting_elements['decisions'][0]
                enhanced_summary += f" Key decision: {decision}."
        
        # Add action items if not already mentioned
        if meeting_elements['action_items']:
            action_keywords = ['will', 'need to', 'follow up', 'action']
            if not any(keyword in enhanced_summary.lower() for keyword in action_keywords):
                action_count = len(meeting_elements['action_items'])
                enhanced_summary += f" {action_count} action item{'s' if action_count > 1 else ''} identified."
        
        return enhanced_summary


def generate_meeting_summary(transcript: str, bart_summary: str) -> str:
    """
    Generate an improved meeting summary using hybrid approach.
    
    Args:
        transcript: Original meeting transcript
        bart_summary: Summary generated by BART
    
    Returns:
        Enhanced meeting summary
    """
    try:
        # Extract meeting-specific elements
        meeting_elements = extract_meeting_elements(transcript)
        
        # Create structured summary
        improved_summary = create_structured_summary(
            bart_summary, 
            meeting_elements, 
            len(transcript)
        )
        
        logger.info(f"Generated hybrid summary: {len(improved_summary)} chars from {len(transcript)} chars")
        return improved_summary
        
    except Exception as e:
        logger.error(f"Error in meeting summary generation: {e}")
        # Fallback to BART summary
        return bart_summary