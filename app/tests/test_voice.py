#!/usr/bin/env python3
"""
Test script for voice service audio conversion
"""

import sys
import os
import logging

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_audio_conversion():
    """Test the audio conversion pipeline"""
    try:
        from app.services.voice_service import generate_arabic_voice
        
        # Test with a simple Arabic phrase
        test_text = "مرحبا"
        print(f"Testing voice generation for: {test_text}")
        
        # Generate audio chunks
        chunks = list(generate_arabic_voice(test_text, gender='female'))
        
        print(f"Generated {len(chunks)} audio chunks")
        
        total_bytes = sum(len(chunk) for chunk in chunks)
        print(f"Total audio data: {total_bytes} bytes")
        
        if len(chunks) > 0:
            print(f"First chunk size: {len(chunks[0])} bytes")
            print(f"Last chunk size: {len(chunks[-1])} bytes")
            print("✅ Audio conversion test PASSED")
        else:
            print("❌ No audio chunks generated")
            
    except Exception as e:
        print(f"❌ Audio conversion test FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_audio_conversion()
