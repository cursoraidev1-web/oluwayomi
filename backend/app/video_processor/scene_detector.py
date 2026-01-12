"""
Scene detection using PySceneDetect (free, open-source).
Identifies scene boundaries to find natural clip points.
"""
import cv2
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass
from scenedetect import detect, ContentDetector, ThresholdDetector, AdaptiveDetector
from scenedetect.video_splitter import split_video_ffmpeg
import logging

logger = logging.getLogger(__name__)


@dataclass
class Scene:
    """Represents a detected scene in the video."""
    start_time: float
    end_time: float
    duration: float
    score: float  # How significant this scene change is (0-100)


class SceneDetector:
    """
    Detects scene changes in videos using multiple algorithms.
    All processing is done locally - no external APIs needed.
    """
    
    def __init__(
        self,
        content_threshold: float = 27.0,
        min_scene_len: int = 15,  # frames
        adaptive_threshold: float = 3.0
    ):
        self.content_threshold = content_threshold
        self.min_scene_len = min_scene_len
        self.adaptive_threshold = adaptive_threshold
    
    def detect_scenes(self, video_path: str) -> List[Scene]:
        """
        Detect scene changes in a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            List of Scene objects with timing information
        """
        try:
            # Use ContentDetector for detecting scene changes based on content
            scene_list = detect(
                video_path,
                ContentDetector(
                    threshold=self.content_threshold,
                    min_scene_len=self.min_scene_len
                )
            )
            
            scenes = []
            for i, (start, end) in enumerate(scene_list):
                start_sec = start.get_seconds()
                end_sec = end.get_seconds()
                duration = end_sec - start_sec
                
                # Calculate a score based on scene duration and position
                # Longer scenes in the middle of the video get higher scores
                position_weight = 1 - abs(0.5 - (start_sec / (scene_list[-1][1].get_seconds() or 1))) * 0.5
                duration_weight = min(duration / 30, 1.0)  # Prefer 30+ second scenes
                score = (position_weight * 50 + duration_weight * 50)
                
                scenes.append(Scene(
                    start_time=start_sec,
                    end_time=end_sec,
                    duration=duration,
                    score=score
                ))
            
            logger.info(f"Detected {len(scenes)} scenes in video")
            return scenes
            
        except Exception as e:
            logger.error(f"Scene detection failed: {e}")
            return []
    
    def detect_with_adaptive(self, video_path: str) -> List[Scene]:
        """
        Use adaptive detection for videos with varying lighting.
        """
        try:
            scene_list = detect(
                video_path,
                AdaptiveDetector(
                    adaptive_threshold=self.adaptive_threshold,
                    min_scene_len=self.min_scene_len
                )
            )
            
            scenes = []
            for start, end in scene_list:
                start_sec = start.get_seconds()
                end_sec = end.get_seconds()
                scenes.append(Scene(
                    start_time=start_sec,
                    end_time=end_sec,
                    duration=end_sec - start_sec,
                    score=50.0
                ))
            
            return scenes
            
        except Exception as e:
            logger.error(f"Adaptive scene detection failed: {e}")
            return []
    
    def get_frame_at_time(self, video_path: str, time_sec: float) -> np.ndarray:
        """Extract a single frame at a specific time."""
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
        ret, frame = cap.read()
        cap.release()
        return frame if ret else None
    
    def calculate_motion_score(
        self, 
        video_path: str, 
        start_time: float, 
        end_time: float,
        sample_rate: int = 5
    ) -> float:
        """
        Calculate motion score for a segment using optical flow.
        Higher motion generally indicates more interesting content.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
        
        motion_scores = []
        prev_gray = None
        
        frame_count = 0
        while cap.get(cv2.CAP_PROP_POS_MSEC) / 1000 < end_time:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            if frame_count % sample_rate != 0:
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_gray is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_gray, gray)
                motion_score = np.mean(diff)
                motion_scores.append(motion_score)
            
            prev_gray = gray
        
        cap.release()
        
        if not motion_scores:
            return 0.0
        
        # Normalize to 0-100 scale
        avg_motion = np.mean(motion_scores)
        return min(avg_motion * 2, 100.0)
