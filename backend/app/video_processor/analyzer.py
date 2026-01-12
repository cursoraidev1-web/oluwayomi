"""
Main video analyzer that combines scene detection and audio analysis
to find the most interesting clips in a video.
"""
import cv2
import numpy as np
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json
import logging

from .scene_detector import SceneDetector, Scene
from .audio_analyzer import AudioAnalyzer, AudioSegment
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ClipCandidate:
    """A candidate clip segment with scoring."""
    start_time: float
    end_time: float
    duration: float
    
    # Individual scores (0-100)
    audio_score: float
    scene_score: float
    motion_score: float
    
    # Combined score
    overall_score: float
    
    # Metadata
    thumbnail_time: float  # Best frame for thumbnail
    description: str = ""


@dataclass
class VideoMetadata:
    """Metadata extracted from video file."""
    duration: float
    width: int
    height: int
    fps: float
    codec: str
    file_size: int
    bitrate: int


class VideoAnalyzer:
    """
    Analyzes videos to find the most interesting clip candidates.
    Uses only free, open-source tools.
    """
    
    def __init__(self):
        self.scene_detector = SceneDetector()
        self.audio_analyzer = AudioAnalyzer()
    
    def get_video_metadata(self, video_path: str) -> Optional[VideoMetadata]:
        """Extract video metadata using FFprobe."""
        try:
            cmd = [
                settings.FFPROBE_PATH,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                return None
            
            format_info = data.get('format', {})
            
            # Parse FPS
            fps_str = video_stream.get('r_frame_rate', '30/1')
            if '/' in fps_str:
                num, den = map(int, fps_str.split('/'))
                fps = num / den if den > 0 else 30
            else:
                fps = float(fps_str)
            
            return VideoMetadata(
                duration=float(format_info.get('duration', 0)),
                width=int(video_stream.get('width', 0)),
                height=int(video_stream.get('height', 0)),
                fps=fps,
                codec=video_stream.get('codec_name', 'unknown'),
                file_size=int(format_info.get('size', 0)),
                bitrate=int(format_info.get('bit_rate', 0))
            )
            
        except Exception as e:
            logger.error(f"Failed to get video metadata: {e}")
            return None
    
    def analyze_video(
        self,
        video_path: str,
        min_clip_duration: float = None,
        max_clip_duration: float = None,
        max_clips: int = None,
        progress_callback=None
    ) -> List[ClipCandidate]:
        """
        Analyze a video and return ranked clip candidates.
        
        Args:
            video_path: Path to video file
            min_clip_duration: Minimum clip length in seconds
            max_clip_duration: Maximum clip length in seconds
            max_clips: Maximum number of clips to return
            progress_callback: Optional callback(progress: int, status: str)
            
        Returns:
            List of ClipCandidate objects sorted by overall score
        """
        min_clip_duration = min_clip_duration or settings.CLIP_MIN_DURATION
        max_clip_duration = max_clip_duration or settings.CLIP_MAX_DURATION
        max_clips = max_clips or settings.MAX_CLIPS_PER_VIDEO
        
        if progress_callback:
            progress_callback(5, "Getting video metadata...")
        
        # Get video metadata
        metadata = self.get_video_metadata(video_path)
        if not metadata:
            logger.error("Could not get video metadata")
            return []
        
        logger.info(f"Video duration: {metadata.duration:.1f}s, {metadata.width}x{metadata.height}")
        
        if progress_callback:
            progress_callback(15, "Detecting scenes...")
        
        # Detect scenes
        scenes = self.scene_detector.detect_scenes(video_path)
        logger.info(f"Detected {len(scenes)} scenes")
        
        if progress_callback:
            progress_callback(35, "Analyzing audio...")
        
        # Analyze audio
        audio_segments = self.audio_analyzer.analyze_audio(video_path)
        audio_peaks = self.audio_analyzer.find_audio_peaks(video_path)
        logger.info(f"Found {len(audio_segments)} audio segments, {len(audio_peaks)} peaks")
        
        if progress_callback:
            progress_callback(55, "Finding interesting moments...")
        
        # Generate clip candidates
        candidates = self._generate_candidates(
            metadata=metadata,
            scenes=scenes,
            audio_segments=audio_segments,
            audio_peaks=audio_peaks,
            min_duration=min_clip_duration,
            max_duration=max_clip_duration
        )
        
        if progress_callback:
            progress_callback(75, "Calculating motion scores...")
        
        # Calculate motion scores for top candidates
        candidates = self._add_motion_scores(
            video_path, 
            candidates[:max_clips * 2]  # Analyze more than needed
        )
        
        if progress_callback:
            progress_callback(90, "Ranking clips...")
        
        # Sort by overall score and return top N
        candidates.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Remove overlapping clips
        final_candidates = self._remove_overlaps(candidates, max_clips)
        
        if progress_callback:
            progress_callback(100, "Analysis complete!")
        
        return final_candidates
    
    def _generate_candidates(
        self,
        metadata: VideoMetadata,
        scenes: List[Scene],
        audio_segments: List[AudioSegment],
        audio_peaks: List[tuple],
        min_duration: float,
        max_duration: float
    ) -> List[ClipCandidate]:
        """Generate clip candidates from analysis data."""
        candidates = []
        
        # Strategy 1: Use scene boundaries with good audio
        for scene in scenes:
            if scene.duration < min_duration:
                continue
            
            # Find best segment within scene
            for audio in audio_segments:
                # Check if audio segment overlaps with scene
                overlap_start = max(scene.start_time, audio.start_time)
                overlap_end = min(scene.end_time, audio.end_time)
                
                if overlap_end - overlap_start >= min_duration:
                    duration = min(overlap_end - overlap_start, max_duration)
                    
                    candidates.append(ClipCandidate(
                        start_time=overlap_start,
                        end_time=overlap_start + duration,
                        duration=duration,
                        audio_score=audio.overall_score,
                        scene_score=scene.score,
                        motion_score=0,  # Will be calculated later
                        overall_score=(audio.overall_score + scene.score) / 2,
                        thumbnail_time=overlap_start + duration / 2
                    ))
        
        # Strategy 2: Build clips around audio peaks
        for peak_time, peak_score in audio_peaks:
            # Center clip around peak
            start = max(0, peak_time - max_duration / 2)
            end = min(metadata.duration, peak_time + max_duration / 2)
            duration = end - start
            
            if duration < min_duration:
                continue
            
            # Find scene score at this time
            scene_score = 50  # Default
            for scene in scenes:
                if scene.start_time <= peak_time <= scene.end_time:
                    scene_score = scene.score
                    break
            
            candidates.append(ClipCandidate(
                start_time=start,
                end_time=end,
                duration=duration,
                audio_score=peak_score,
                scene_score=scene_score,
                motion_score=0,
                overall_score=(peak_score + scene_score) / 2,
                thumbnail_time=peak_time
            ))
        
        # Strategy 3: Sliding window for uniform coverage
        window_size = max_duration
        step = window_size / 2
        
        for start in np.arange(0, metadata.duration - min_duration, step):
            end = min(start + window_size, metadata.duration)
            duration = end - start
            
            if duration < min_duration:
                continue
            
            # Calculate audio score for this window
            audio_score = 0
            for audio in audio_segments:
                overlap = min(audio.end_time, end) - max(audio.start_time, start)
                if overlap > 0:
                    audio_score = max(audio_score, audio.overall_score)
            
            # Calculate scene score
            scene_score = 50
            for scene in scenes:
                if scene.start_time <= start + duration / 2 <= scene.end_time:
                    scene_score = scene.score
                    break
            
            candidates.append(ClipCandidate(
                start_time=start,
                end_time=end,
                duration=duration,
                audio_score=audio_score,
                scene_score=scene_score,
                motion_score=0,
                overall_score=(audio_score + scene_score) / 2,
                thumbnail_time=start + duration / 2
            ))
        
        return candidates
    
    def _add_motion_scores(
        self, 
        video_path: str, 
        candidates: List[ClipCandidate]
    ) -> List[ClipCandidate]:
        """Add motion scores to candidates."""
        for candidate in candidates:
            motion_score = self.scene_detector.calculate_motion_score(
                video_path,
                candidate.start_time,
                candidate.end_time
            )
            candidate.motion_score = motion_score
            
            # Recalculate overall score with motion
            candidate.overall_score = (
                candidate.audio_score * 0.35 +
                candidate.scene_score * 0.30 +
                candidate.motion_score * 0.35
            )
        
        return candidates
    
    def _remove_overlaps(
        self, 
        candidates: List[ClipCandidate], 
        max_clips: int
    ) -> List[ClipCandidate]:
        """Remove overlapping clips, keeping higher scored ones."""
        final = []
        
        for candidate in candidates:
            # Check overlap with existing clips
            overlaps = False
            for existing in final:
                overlap_start = max(candidate.start_time, existing.start_time)
                overlap_end = min(candidate.end_time, existing.end_time)
                
                if overlap_end > overlap_start:
                    overlap_duration = overlap_end - overlap_start
                    # If more than 50% overlap, skip
                    if overlap_duration > min(candidate.duration, existing.duration) * 0.5:
                        overlaps = True
                        break
            
            if not overlaps:
                final.append(candidate)
                if len(final) >= max_clips:
                    break
        
        return final
