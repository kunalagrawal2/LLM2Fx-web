#!/usr/bin/env python3
"""
Test script to verify audio processing is working
"""
import numpy as np
import soundfile as sf
from app.audio_processor import AudioProcessor, process_audio_with_effects
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_audio(duration=3.0, sample_rate=44100):
    """Create a simple test audio signal"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Create a simple sine wave with some harmonics
    signal = np.sin(2 * np.pi * 440 * t) + 0.5 * np.sin(2 * np.pi * 880 * t)
    return signal, sample_rate

def test_audio_processing():
    """Test the audio processing with a simple signal"""
    logger.info("Creating test audio...")
    
    # Create test audio
    audio, sr = create_test_audio()
    
    # Save original
    sf.write("test_original.wav", audio, sr)
    logger.info("Saved test_original.wav")
    
    # Test effects parameters
    effects_params = {
        "reverb": {
            "gains_db": [3.0] * 12,  # 3dB gain for all bands
            "decays_s": [2.0] * 12,  # 2 second decay
            "mix": 0.7  # 70% wet
        }
    }
    
    logger.info("Processing audio with effects...")
    success = process_audio_with_effects("test_original.wav", "test_processed.wav", effects_params)
    
    if success:
        logger.info("✅ Audio processing successful!")
        logger.info("Check test_original.wav vs test_processed.wav")
    else:
        logger.error("❌ Audio processing failed!")

if __name__ == "__main__":
    test_audio_processing()
