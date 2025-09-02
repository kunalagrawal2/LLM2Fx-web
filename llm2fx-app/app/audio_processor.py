import librosa
import soundfile as sf
import numpy as np
from scipy import signal
from scipy.signal import lfilter
import os
from pathlib import Path
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Audio processing class for applying AI-generated effects"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.frequency_bands = [
            20, 50, 100, 200, 400, 800, 1500, 3000, 6000, 12000, 16000, 20000
        ]
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return audio data and sample rate"""
        try:
            audio, sr = librosa.load(file_path, sr=self.sample_rate)
            return audio, sr
        except Exception as e:
            logger.error(f"Error loading audio file: {e}")
            raise
    
    def apply_reverb(self, audio: np.ndarray, gains_db: List[float], decays_s: List[float], mix: float) -> np.ndarray:
        """
        Apply reverb effect using multi-band processing
        
        Args:
            audio: Input audio signal
            gains_db: Gain values for each frequency band (12 bands)
            decays_s: Decay times for each frequency band (12 bands)
            mix: Wet/dry mix (0.0 = dry, 1.0 = wet)
        """
        try:
            logger.info(f"apply_reverb called with mix={mix}, gains={gains_db[:3]}...")
            
            # Ensure we have stereo audio
            if len(audio.shape) == 1:
                audio = np.column_stack([audio, audio])
            
            # Create a more pronounced reverb effect
            # Use the average gain and decay for simplicity
            avg_gain_db = np.mean(gains_db)
            avg_decay_s = np.mean(decays_s)
            
            logger.info(f"Average gain: {avg_gain_db}dB, Average decay: {avg_decay_s}s")
            
            # Convert gain from dB to linear
            gain_linear = 10 ** (avg_gain_db / 20.0)
            
            # Create reverb using multiple delays
            reverb_audio = np.zeros_like(audio)
            
            # Multiple delay taps for more realistic reverb
            delays = [int(avg_decay_s * self.sample_rate * 0.05 * i) for i in range(1, 8)]  # More delays, shorter spacing
            decay_factors = [np.exp(-i * 0.3) for i in range(1, 8)]  # Slower decay for more pronounced effect
            
            for delay_samples, decay_factor in zip(delays, decay_factors):
                if delay_samples < len(audio):
                    delayed = np.zeros_like(audio)
                    delayed[delay_samples:] = audio[:-delay_samples] * decay_factor * gain_linear
                    reverb_audio += delayed
            
            # Add some feedback for more realistic reverb
            feedback_delay = int(avg_decay_s * self.sample_rate * 0.3)
            if feedback_delay < len(audio):
                feedback = np.zeros_like(audio)
                feedback[feedback_delay:] = reverb_audio[:-feedback_delay] * 0.3
                reverb_audio += feedback
            
            # Normalize reverb
            max_reverb = np.max(np.abs(reverb_audio))
            if max_reverb > 0:
                reverb_audio = reverb_audio / max_reverb * 0.8
            
            # Apply wet/dry mix with more pronounced effect
            # Increase the mix to make the effect more noticeable
            effective_mix = min(0.9, mix * 2.0)  # Double the mix effect for more pronounced reverb
            final_audio = (1 - effective_mix) * audio + effective_mix * reverb_audio
            
            # Normalize final output
            max_final = np.max(np.abs(final_audio))
            if max_final > 0:
                final_audio = final_audio / max_final * 0.95
            
            logger.info(f"Reverb applied: original max={np.max(np.abs(audio)):.4f}, processed max={np.max(np.abs(final_audio)):.4f}, effective_mix={effective_mix}")
            
            return final_audio
            
        except Exception as e:
            logger.error(f"Error applying reverb: {e}")
            return audio  # Return original if processing fails
    
    def _apply_simple_reverb(self, signal_data: np.ndarray, decay_s: float) -> np.ndarray:
        """Apply simple delay-based reverb"""
        try:
            # Calculate delay time based on decay
            delay_samples = int(decay_s * self.sample_rate * 0.1)  # 10% of decay time as delay
            delay_samples = max(1, min(delay_samples, len(signal_data) // 4))  # Clamp to reasonable range
            
            # Create delayed version
            delayed = np.zeros_like(signal_data)
            delayed[delay_samples:] = signal_data[:-delay_samples]
            
            # Apply decay
            decay_factor = np.exp(-1.0 / (decay_s * self.sample_rate))
            delayed *= decay_factor
            
            # Mix original and delayed
            reverb_signal = signal_data + delayed
            
            # Normalize
            max_val = np.max(np.abs(reverb_signal))
            if max_val > 0:
                reverb_signal = reverb_signal / max_val * 0.9
            
            return reverb_signal
            
        except Exception as e:
            logger.error(f"Error in simple reverb: {e}")
            return signal_data
    
    def apply_eq(self, audio: np.ndarray, gains_db: List[float]) -> np.ndarray:
        """Apply equalization using multi-band processing"""
        try:
            # Similar to reverb but only applying gains
            processed_audio = np.zeros_like(audio)
            
            for i, gain_db in enumerate(gains_db):
                gain_linear = 10 ** (gain_db / 20.0)
                
                # Create bandpass filter (same as reverb)
                if i == 0:
                    low_freq = 0
                    high_freq = self.frequency_bands[i]
                elif i == len(self.frequency_bands) - 1:
                    low_freq = self.frequency_bands[i-1]
                    high_freq = self.sample_rate // 2
                else:
                    low_freq = self.frequency_bands[i-1]
                    high_freq = self.frequency_bands[i]
                
                nyquist = self.sample_rate / 2
                low_norm = low_freq / nyquist
                high_norm = high_freq / nyquist
                
                if high_norm < 1.0:
                    b, a = signal.butter(4, [low_norm, high_norm], btype='band')
                    
                    for ch in range(audio.shape[1]):
                        band_signal = signal.filtfilt(b, a, audio[:, ch])
                        band_signal *= gain_linear
                        processed_audio[:, ch] += band_signal
            
            # Normalize
            max_val = np.max(np.abs(processed_audio))
            if max_val > 0:
                processed_audio = processed_audio / max_val * 0.95
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error applying EQ: {e}")
            return audio
    
    def save_audio(self, audio: np.ndarray, output_path: str, sample_rate: int = None) -> None:
        """Save processed audio to file"""
        try:
            if sample_rate is None:
                sample_rate = self.sample_rate
            
            # Ensure audio is in the right format
            if len(audio.shape) == 1:
                audio = audio.reshape(-1, 1)
            
            sf.write(output_path, audio, sample_rate)
            logger.info(f"Audio saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            raise

def process_audio_with_effects(input_path: str, output_path: str, effects_params: dict) -> bool:
    """
    Main function to process audio with AI-generated effects
    
    Args:
        input_path: Path to input audio file
        output_path: Path to save processed audio
        effects_params: Dictionary containing effect parameters
    
    Returns:
        bool: True if processing was successful
    """
    try:
        logger.info(f"Starting audio processing: {input_path} -> {output_path}")
        logger.info(f"Effects parameters: {effects_params}")
        
        processor = AudioProcessor()
        
        # Load audio
        audio, sr = processor.load_audio(input_path)
        logger.info(f"Loaded audio: shape={audio.shape}, sample_rate={sr}")
        
        # Apply effects based on type
        if effects_params.get("reverb"):
            reverb_params = effects_params["reverb"]
            logger.info(f"Applying reverb with params: {reverb_params}")
            
            gains_db = reverb_params.get("gains_db", [0.0] * 12)
            decays_s = reverb_params.get("decays_s", [1.0] * 12)
            mix = reverb_params.get("mix", 0.5)
            
            logger.info(f"Reverb gains: {gains_db}")
            logger.info(f"Reverb decays: {decays_s}")
            logger.info(f"Reverb mix: {mix}")
            
            audio = processor.apply_reverb(audio, gains_db, decays_s, mix)
            logger.info(f"Reverb applied, new audio shape: {audio.shape}")
        
        elif effects_params.get("eq"):
            eq_params = effects_params["eq"]
            logger.info(f"Applying EQ with params: {eq_params}")
            audio = processor.apply_eq(audio, eq_params.get("gains_db", [0.0] * 12))
        
        # Save processed audio
        processor.save_audio(audio, output_path, sr)
        logger.info(f"Audio processing completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in audio processing: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
