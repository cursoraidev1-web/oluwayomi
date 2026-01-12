import os
import yt_dlp
import logging
import ffmpeg
from faster_whisper import WhisperModel
import nltk
from nltk.tokenize import sent_tokenize
import numpy as np
from .social_poster import post_to_socials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize model once (lazy load might be better if memory is tight, but this is simpler)
# 'tiny' or 'base' is good for CPU/no-maintenance. 'small' is better accuracy.
MODEL_SIZE = "tiny" 

def process_video_task(url, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    logger.info(f"Starting processing for {url}")
    
    try:
        # 1. Download Video
        video_path = download_video(url, output_folder)
        if not video_path:
            logger.error("Failed to download video")
            return

        logger.info(f"Video downloaded to {video_path}")

        # 2. Transcribe
        logger.info("Starting transcription...")
        segments = transcribe_video(video_path)
        
        # 3. Identify Important Clips
        logger.info("Analyzing content for clips...")
        clips_to_make = analyze_transcript(segments)
        
        # 4. Cut Clips
        logger.info(f"Cutting {len(clips_to_make)} clips...")
        created_clips = cut_clips(video_path, clips_to_make, output_folder)
        
        # 5. Post to Socials
        for clip in created_clips:
            post_to_socials(clip)
            
        logger.info("Processing complete.")
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}", exc_info=True)

def download_video(url, output_folder):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_folder, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_filename = ydl.prepare_filename(info_dict)
        return video_filename

def transcribe_video(video_path):
    # Run on CPU with INT8/float32 (compatible with most cheap hosting/local machines)
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(video_path, beam_size=5)
    
    # Convert generator to list for analysis
    segment_list = []
    for segment in segments:
        segment_list.append({
            'start': segment.start,
            'end': segment.end,
            'text': segment.text
        })
    
    return segment_list

def analyze_transcript(segments):
    """
    Simple heuristic: Select segments that form complete sentences and are somewhat long (15-60s).
    A better approach would use TF-IDF or textrank, but this is a "no maintenance" start.
    We will group segments into ~30-60s chunks and pick the "densest" ones (most words per second?).
    """
    
    # Flatten text to sentences while keeping time mapping
    # This is tricky because whisper segments might not align perfectly with sentences.
    # Simplified approach: Group segments into ~45s blocks with 15s overlap.
    
    clips = []
    window_size = 45 # seconds
    step = 30 # seconds
    
    if not segments:
        return []

    video_duration = segments[-1]['end']
    
    current_time = 0
    while current_time < video_duration:
        window_end = current_time + window_size
        
        # Find segments that fall mostly within this window
        window_segments = [s for s in segments if s['start'] >= current_time and s['end'] <= window_end]
        
        if window_segments:
            # Construct text
            text = " ".join([s['text'] for s in window_segments]).strip()
            
            # Basic score: length of text (talking density)
            # Avoid empty or silent parts
            if len(text) > 50: 
                clips.append({
                    'start': window_segments[0]['start'],
                    'end': window_segments[-1]['end'],
                    'text': text,
                    'score': len(text) # Simple score: more talking = more info
                })
        
        current_time += step
        
    # Sort by score and pick top 3, ensuring no overlap (simplified: just pick top 3 for now)
    clips.sort(key=lambda x: x['score'], reverse=True)
    return clips[:3]

def cut_clips(video_path, clips_data, output_folder):
    generated_files = []
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    
    for i, clip in enumerate(clips_data):
        start = clip['start']
        duration = clip['end'] - clip['start']
        output_filename = f"{base_name}_clip_{i+1}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        try:
            (
                ffmpeg
                .input(video_path, ss=start, t=duration)
                .output(output_path, c='copy') # 'copy' is fast/lossless but might not be frame-perfect. re-encode for precision: vcodec='libx264', acodec='aac'
                .overwrite_output()
                .run(quiet=True)
            )
            generated_files.append({
                'path': output_path,
                'caption': generate_caption(clip['text'])
            })
        except Exception as e:
            logger.error(f"Error cutting clip {i}: {e}")
            
    return generated_files

def generate_caption(text):
    # Truncate text for caption
    if len(text) > 200:
        return text[:197] + "..."
    return text
