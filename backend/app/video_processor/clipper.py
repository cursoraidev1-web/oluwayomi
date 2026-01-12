"""
Video clipper using FFmpeg (free, open-source).
Extracts clips from videos based on timestamps.
"""
import subprocess
import os
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
import logging
import uuid

from app.config import settings
from .analyzer import ClipCandidate

logger = logging.getLogger(__name__)


@dataclass
class ClipResult:
    """Result of clip extraction."""
    success: bool
    clip_path: str
    thumbnail_path: str
    error: Optional[str] = None


class VideoClipper:
    """
    Extracts video clips using FFmpeg.
    All processing is local - no external services needed.
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or settings.CLIPS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_clip(
        self,
        source_path: str,
        start_time: float,
        end_time: float,
        output_name: str = None,
        optimize_for_social: bool = True
    ) -> ClipResult:
        """
        Extract a clip from a video.
        
        Args:
            source_path: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_name: Optional output filename (without extension)
            optimize_for_social: Apply social media optimizations
            
        Returns:
            ClipResult with paths to clip and thumbnail
        """
        try:
            duration = end_time - start_time
            output_name = output_name or f"clip_{uuid.uuid4().hex[:8]}"
            
            clip_path = self.output_dir / f"{output_name}.mp4"
            thumbnail_path = self.output_dir / f"{output_name}_thumb.jpg"
            
            # Build FFmpeg command
            cmd = [settings.FFMPEG_PATH]
            
            # Input seeking (fast)
            cmd.extend(['-ss', str(start_time)])
            cmd.extend(['-i', source_path])
            cmd.extend(['-t', str(duration)])
            
            if optimize_for_social:
                # Optimize for social media platforms
                cmd.extend([
                    # Video codec
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23',
                    
                    # Audio codec
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    
                    # Ensure compatibility
                    '-movflags', '+faststart',
                    '-pix_fmt', 'yuv420p',
                    
                    # Cap resolution for smaller files
                    '-vf', 'scale=min(1080\\,iw):min(1920\\,ih):force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2',
                ])
            else:
                # Quick copy without re-encoding
                cmd.extend(['-c', 'copy'])
            
            cmd.extend(['-y', str(clip_path)])
            
            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract thumbnail
            thumb_time = start_time + duration / 2
            self._extract_thumbnail(source_path, thumb_time, thumbnail_path)
            
            return ClipResult(
                success=True,
                clip_path=str(clip_path),
                thumbnail_path=str(thumbnail_path)
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr}")
            return ClipResult(
                success=False,
                clip_path="",
                thumbnail_path="",
                error=f"FFmpeg error: {e.stderr}"
            )
        except Exception as e:
            logger.error(f"Clip extraction failed: {e}")
            return ClipResult(
                success=False,
                clip_path="",
                thumbnail_path="",
                error=str(e)
            )
    
    def _extract_thumbnail(
        self, 
        source_path: str, 
        time_sec: float, 
        output_path: Path
    ) -> bool:
        """Extract a thumbnail frame from video."""
        try:
            cmd = [
                settings.FFMPEG_PATH,
                '-ss', str(time_sec),
                '-i', source_path,
                '-vframes', '1',
                '-q:v', '2',
                '-y', str(output_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except Exception as e:
            logger.error(f"Thumbnail extraction failed: {e}")
            return False
    
    def extract_clips_from_candidates(
        self,
        source_path: str,
        candidates: List[ClipCandidate],
        progress_callback=None
    ) -> List[ClipResult]:
        """
        Extract multiple clips from candidates.
        
        Args:
            source_path: Path to source video
            candidates: List of ClipCandidate objects
            progress_callback: Optional callback(progress: int, clip_num: int)
            
        Returns:
            List of ClipResult objects
        """
        results = []
        total = len(candidates)
        
        for i, candidate in enumerate(candidates):
            if progress_callback:
                progress = int((i / total) * 100)
                progress_callback(progress, i + 1)
            
            result = self.extract_clip(
                source_path=source_path,
                start_time=candidate.start_time,
                end_time=candidate.end_time,
                optimize_for_social=True
            )
            
            results.append(result)
        
        return results
    
    def create_vertical_clip(
        self,
        source_path: str,
        start_time: float,
        end_time: float,
        output_name: str = None
    ) -> ClipResult:
        """
        Create a vertical (9:16) clip for TikTok/Reels/Shorts.
        Uses smart cropping to focus on center of action.
        """
        try:
            duration = end_time - start_time
            output_name = output_name or f"vertical_{uuid.uuid4().hex[:8]}"
            clip_path = self.output_dir / f"{output_name}.mp4"
            thumbnail_path = self.output_dir / f"{output_name}_thumb.jpg"
            
            # Create vertical video (9:16 aspect ratio, 1080x1920)
            cmd = [
                settings.FFMPEG_PATH,
                '-ss', str(start_time),
                '-i', source_path,
                '-t', str(duration),
                
                # Video settings for vertical format
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                
                # Crop to vertical - center crop
                '-vf', 'crop=ih*9/16:ih,scale=1080:1920',
                
                # Audio
                '-c:a', 'aac',
                '-b:a', '128k',
                
                # Compatibility
                '-movflags', '+faststart',
                '-pix_fmt', 'yuv420p',
                
                '-y', str(clip_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Extract thumbnail
            self._extract_thumbnail(source_path, start_time + duration / 2, thumbnail_path)
            
            return ClipResult(
                success=True,
                clip_path=str(clip_path),
                thumbnail_path=str(thumbnail_path)
            )
            
        except Exception as e:
            logger.error(f"Vertical clip creation failed: {e}")
            return ClipResult(
                success=False,
                clip_path="",
                thumbnail_path="",
                error=str(e)
            )
    
    def add_text_overlay(
        self,
        clip_path: str,
        text: str,
        position: str = "bottom",
        font_size: int = 32,
        output_path: str = None
    ) -> ClipResult:
        """
        Add text overlay to a clip.
        
        Args:
            clip_path: Path to input clip
            text: Text to overlay
            position: Position (top, center, bottom)
            font_size: Font size in pixels
            output_path: Output path (default: overwrites input)
        """
        try:
            output_path = output_path or clip_path.replace('.mp4', '_text.mp4')
            
            # Position mapping
            positions = {
                'top': 'x=(w-text_w)/2:y=50',
                'center': 'x=(w-text_w)/2:y=(h-text_h)/2',
                'bottom': 'x=(w-text_w)/2:y=h-text_h-50'
            }
            
            pos = positions.get(position, positions['bottom'])
            
            # Escape special characters in text
            safe_text = text.replace("'", "\\'").replace(":", "\\:")
            
            cmd = [
                settings.FFMPEG_PATH,
                '-i', clip_path,
                '-vf', f"drawtext=text='{safe_text}':fontsize={font_size}:fontcolor=white:borderw=2:bordercolor=black:{pos}",
                '-c:a', 'copy',
                '-y', output_path
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            return ClipResult(
                success=True,
                clip_path=output_path,
                thumbnail_path=""
            )
            
        except Exception as e:
            logger.error(f"Text overlay failed: {e}")
            return ClipResult(
                success=False,
                clip_path="",
                thumbnail_path="",
                error=str(e)
            )
