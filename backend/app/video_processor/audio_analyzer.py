"""
Audio analysis for detecting interesting moments in videos.
Uses librosa (free, open-source) for audio processing.
"""
import numpy as np
import librosa
from typing import List, Tuple
from dataclasses import dataclass
import subprocess
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """Represents an interesting audio segment."""
    start_time: float
    end_time: float
    duration: float
    loudness_score: float  # 0-100
    speech_score: float  # 0-100
    music_score: float  # 0-100
    energy_score: float  # 0-100
    overall_score: float  # Combined score 0-100


class AudioAnalyzer:
    """
    Analyzes audio to find interesting moments in videos.
    All processing is done locally using librosa.
    """
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
    
    def extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video using FFmpeg.
        Returns path to temporary audio file.
        """
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio.close()
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', str(self.sample_rate),
            '-ac', '1',
            '-y', temp_audio.name
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return temp_audio.name
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio extraction failed: {e}")
            if os.path.exists(temp_audio.name):
                os.unlink(temp_audio.name)
            return None
    
    def analyze_audio(self, video_path: str, segment_duration: float = 5.0) -> List[AudioSegment]:
        """
        Analyze video audio and return interesting segments.
        
        Args:
            video_path: Path to video file
            segment_duration: Duration of analysis segments in seconds
            
        Returns:
            List of AudioSegment objects sorted by interest score
        """
        audio_path = self.extract_audio(video_path)
        if not audio_path:
            return []
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            total_duration = len(y) / sr
            
            segments = []
            
            # Analyze in segments
            for start in np.arange(0, total_duration - segment_duration, segment_duration / 2):
                end = min(start + segment_duration, total_duration)
                
                start_sample = int(start * sr)
                end_sample = int(end * sr)
                segment_audio = y[start_sample:end_sample]
                
                if len(segment_audio) < sr:  # Skip very short segments
                    continue
                
                # Calculate various audio features
                loudness = self._calculate_loudness(segment_audio)
                energy = self._calculate_energy(segment_audio)
                speech_likelihood = self._detect_speech_likelihood(segment_audio, sr)
                music_likelihood = self._detect_music_likelihood(segment_audio, sr)
                
                # Calculate overall score
                overall_score = (
                    loudness * 0.3 +
                    energy * 0.3 +
                    speech_likelihood * 0.25 +
                    music_likelihood * 0.15
                )
                
                segments.append(AudioSegment(
                    start_time=start,
                    end_time=end,
                    duration=end - start,
                    loudness_score=loudness,
                    speech_score=speech_likelihood,
                    music_score=music_likelihood,
                    energy_score=energy,
                    overall_score=overall_score
                ))
            
            # Sort by overall score
            segments.sort(key=lambda x: x.overall_score, reverse=True)
            
            return segments
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return []
        finally:
            # Cleanup temp file
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
    
    def _calculate_loudness(self, audio: np.ndarray) -> float:
        """Calculate perceived loudness (0-100)."""
        rms = np.sqrt(np.mean(audio ** 2))
        # Convert to dB and normalize
        if rms > 0:
            db = 20 * np.log10(rms)
            # Typical range is -60 to 0 dB
            normalized = (db + 60) / 60 * 100
            return max(0, min(100, normalized))
        return 0
    
    def _calculate_energy(self, audio: np.ndarray) -> float:
        """Calculate audio energy variance (indicates dynamic content)."""
        # Calculate short-term energy
        frame_length = 2048
        hop_length = 512
        
        energy = np.array([
            np.sum(audio[i:i + frame_length] ** 2)
            for i in range(0, len(audio) - frame_length, hop_length)
        ])
        
        if len(energy) == 0:
            return 0
        
        # High variance = dynamic content = more interesting
        variance = np.var(energy)
        mean_energy = np.mean(energy)
        
        if mean_energy > 0:
            # Coefficient of variation
            cv = np.sqrt(variance) / mean_energy
            return min(cv * 50, 100)
        return 0
    
    def _detect_speech_likelihood(self, audio: np.ndarray, sr: int) -> float:
        """
        Estimate speech likelihood using spectral features.
        Speech typically has specific spectral characteristics.
        """
        try:
            # Calculate spectral centroid
            centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            mean_centroid = np.mean(centroid)
            
            # Speech typically has centroid between 500-3000 Hz
            # Normalize based on typical speech range
            if 500 <= mean_centroid <= 3000:
                speech_score = 100 - abs(mean_centroid - 1500) / 15
            else:
                speech_score = max(0, 50 - abs(mean_centroid - 1500) / 30)
            
            # Zero crossing rate (speech has moderate ZCR)
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            mean_zcr = np.mean(zcr)
            
            # Typical speech ZCR is 0.05-0.15
            if 0.05 <= mean_zcr <= 0.15:
                zcr_score = 100
            else:
                zcr_score = max(0, 100 - abs(mean_zcr - 0.1) * 500)
            
            return (speech_score + zcr_score) / 2
            
        except Exception:
            return 50  # Default middle score
    
    def _detect_music_likelihood(self, audio: np.ndarray, sr: int) -> float:
        """
        Estimate music likelihood using rhythm and harmonic features.
        """
        try:
            # Tempo estimation
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            
            # Music typically has clear tempo between 60-180 BPM
            if isinstance(tempo, np.ndarray):
                tempo = tempo[0] if len(tempo) > 0 else 0
            
            if 60 <= tempo <= 180:
                tempo_score = 100
            else:
                tempo_score = max(0, 100 - abs(tempo - 120) / 2)
            
            # Harmonic content
            harmonic = librosa.effects.harmonic(audio)
            harmonic_ratio = np.sum(harmonic ** 2) / (np.sum(audio ** 2) + 1e-10)
            harmonic_score = min(harmonic_ratio * 100, 100)
            
            return (tempo_score + harmonic_score) / 2
            
        except Exception:
            return 50  # Default middle score
    
    def find_audio_peaks(
        self, 
        video_path: str, 
        num_peaks: int = 10,
        min_distance_sec: float = 10.0
    ) -> List[Tuple[float, float]]:
        """
        Find peak moments in audio (loud, energetic).
        
        Returns:
            List of (timestamp, score) tuples
        """
        audio_path = self.extract_audio(video_path)
        if not audio_path:
            return []
        
        try:
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Calculate RMS energy over time
            rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
            
            # Convert frame indices to time
            times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
            
            # Find peaks
            peaks = []
            min_distance_frames = int(min_distance_sec * sr / 512)
            
            for i in range(1, len(rms) - 1):
                if rms[i] > rms[i-1] and rms[i] > rms[i+1]:
                    # Check minimum distance from existing peaks
                    if all(abs(i - p[0]) > min_distance_frames for p in peaks):
                        peaks.append((i, rms[i]))
            
            # Sort by amplitude and take top N
            peaks.sort(key=lambda x: x[1], reverse=True)
            peaks = peaks[:num_peaks]
            
            # Convert to timestamps and normalize scores
            max_rms = max(rms) if len(rms) > 0 else 1
            result = [
                (times[p[0]], (p[1] / max_rms) * 100)
                for p in peaks
            ]
            
            return sorted(result, key=lambda x: x[0])
            
        except Exception as e:
            logger.error(f"Peak detection failed: {e}")
            return []
        finally:
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
