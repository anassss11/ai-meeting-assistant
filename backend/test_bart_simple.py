#!/usr/bin/env python3
"""
Simple test script to check BART model performance and timing.
"""

import time
import os
import sys

# Set the environment variable to avoid OpenMP issues
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def test_bart_summary():
    """Test BART summarization with timing."""
    try:
        print("🔍 Testing BART Model Performance...")
        
        # Import after setting environment variable
        from bart_config import BARTConfig
        from bart_fallback import FallbackHandler
        from bart_summarizer import generate_bart_summary
        
        # Read the transcript
        with open('transcripts/meeting.txt', 'r', encoding='utf-8') as f:
            transcript = f.read().strip()
        
        print(f"📝 Transcript length: {len(transcript)} characters")
        
        # Initialize configuration
        config = BARTConfig.from_env()
        config.validate()
        fallback_handler = FallbackHandler(config)
        
        print(f"⚙️  BART Config: device={config.device}, max_length={config.max_length}")
        
        # Time the summarization
        start_time = time.time()
        print("🤖 Starting BART summarization...")
        
        summary = generate_bart_summary(transcript, config, fallback_handler)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Summary generated in {duration:.2f} seconds")
        print(f"📄 Summary length: {len(summary)} characters")
        print(f"📋 Summary: {summary}")
        
        # Check if fallback was used
        metrics = fallback_handler.get_metrics()
        if metrics['fallback_requests'] > 0:
            print("⚠️  Fallback was used - BART may have failed")
        else:
            print("✅ BART processed successfully")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_bart_summary()
    sys.exit(0 if success else 1)