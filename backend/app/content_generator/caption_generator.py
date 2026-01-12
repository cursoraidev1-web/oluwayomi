"""
Caption generator for social media posts.
Uses template-based generation with keyword extraction - no paid APIs needed.
"""
import re
from typing import List, Optional, Dict
from dataclasses import dataclass
import random


@dataclass
class CaptionConfig:
    """Configuration for caption generation."""
    max_length: int = 280  # Twitter limit
    include_cta: bool = True  # Call to action
    include_emoji: bool = True
    tone: str = "engaging"  # engaging, professional, casual, funny


class CaptionGenerator:
    """
    Generates engaging captions for video clips.
    Template-based approach - no external API dependencies.
    """
    
    # Caption templates by category
    TEMPLATES = {
        "general": [
            "Check out this moment! {emoji}",
            "You need to see this {emoji}",
            "Wait for it... {emoji}",
            "This is incredible! {emoji}",
            "{emoji} Can't believe this happened!",
            "The moment that changed everything {emoji}",
            "Pure gold right here {emoji}",
            "This deserves more attention {emoji}",
            "Dropping this gem {emoji}",
        ],
        "gaming": [
            "That play was INSANE! {emoji}",
            "Gaming moment of the day {emoji}",
            "When everything just clicks {emoji}",
            "Pro move right there {emoji}",
            "GG! What a play {emoji}",
        ],
        "sports": [
            "What a moment! {emoji}",
            "The crowd went wild! {emoji}",
            "Athletic excellence {emoji}",
            "That's how it's done! {emoji}",
            "Peak performance {emoji}",
        ],
        "music": [
            "When the beat drops {emoji}",
            "Music to your ears {emoji}",
            "This hits different {emoji}",
            "Can't stop replaying this {emoji}",
            "Pure vibes {emoji}",
        ],
        "comedy": [
            "I can't stop laughing {emoji}",
            "This is too funny {emoji}",
            "Comedy gold {emoji}",
            "Try not to laugh {emoji}",
            "Had to share this {emoji}",
        ],
        "educational": [
            "Did you know this? {emoji}",
            "Learn something new today {emoji}",
            "Mind = blown {emoji}",
            "Knowledge drop {emoji}",
            "The more you know {emoji}",
        ],
        "motivational": [
            "Let this inspire you {emoji}",
            "Success in action {emoji}",
            "This is what dedication looks like {emoji}",
            "Never give up {emoji}",
            "Pushing boundaries {emoji}",
        ]
    }
    
    # Call-to-action phrases
    CTAS = [
        "Like if you agree!",
        "Drop a comment below!",
        "Share with someone who needs to see this!",
        "Save this for later!",
        "Follow for more!",
        "Double tap if you love this!",
        "What do you think?",
        "Tag a friend!",
    ]
    
    # Emoji sets by category
    EMOJIS = {
        "general": ["🔥", "✨", "💯", "🙌", "⚡", "🎯", "💪", "🚀"],
        "gaming": ["🎮", "🕹️", "🏆", "💥", "⚔️", "🎯", "👾", "🔥"],
        "sports": ["🏆", "💪", "⚽", "🏀", "🎾", "🏃", "🔥", "👏"],
        "music": ["🎵", "🎶", "🎤", "🎧", "🎸", "🔊", "💫", "✨"],
        "comedy": ["😂", "🤣", "😆", "💀", "😭", "🤪", "😜", "🙈"],
        "educational": ["📚", "💡", "🧠", "📖", "🎓", "✍️", "💭", "🔍"],
        "motivational": ["💪", "🏆", "⭐", "🌟", "🚀", "✨", "🔥", "💯"]
    }
    
    # Keywords that indicate content category
    CATEGORY_KEYWORDS = {
        "gaming": ["game", "play", "stream", "twitch", "xbox", "playstation", "pc", "gamer", 
                   "fortnite", "minecraft", "league", "valorant", "apex", "cod", "gaming"],
        "sports": ["sport", "football", "basketball", "soccer", "tennis", "golf", "athlete",
                   "workout", "fitness", "gym", "training", "match", "game", "score"],
        "music": ["music", "song", "artist", "singer", "band", "concert", "album", "track",
                  "beat", "melody", "dj", "remix", "cover", "live", "performance"],
        "comedy": ["funny", "comedy", "laugh", "joke", "humor", "hilarious", "lol", "meme",
                   "prank", "sketch", "standup", "comedian"],
        "educational": ["learn", "education", "tutorial", "how to", "explain", "science",
                        "history", "fact", "tip", "guide", "lesson", "course"],
        "motivational": ["motivat", "inspir", "success", "goal", "dream", "achieve",
                         "mindset", "growth", "hustle", "grind"]
    }
    
    def __init__(self, config: CaptionConfig = None):
        self.config = config or CaptionConfig()
    
    def generate_caption(
        self,
        title: str = "",
        description: str = "",
        tags: List[str] = None,
        platform: str = "general"  # twitter, instagram, tiktok, youtube
    ) -> str:
        """
        Generate a caption based on video metadata.
        
        Args:
            title: Video title
            description: Video description
            tags: Video tags
            platform: Target platform
            
        Returns:
            Generated caption string
        """
        tags = tags or []
        
        # Detect content category
        all_text = f"{title} {description} {' '.join(tags)}".lower()
        category = self._detect_category(all_text)
        
        # Select template
        templates = self.TEMPLATES.get(category, self.TEMPLATES["general"])
        template = random.choice(templates)
        
        # Select emoji
        emojis = self.EMOJIS.get(category, self.EMOJIS["general"])
        emoji = random.choice(emojis) if self.config.include_emoji else ""
        
        # Build caption
        caption = template.format(emoji=emoji)
        
        # Add title/keywords if available and fits
        if title:
            clean_title = self._clean_title(title)
            if len(caption) + len(clean_title) + 5 < self.config.max_length:
                caption = f"{clean_title}\n\n{caption}"
        
        # Add CTA if enabled and fits
        if self.config.include_cta:
            cta = random.choice(self.CTAS)
            if len(caption) + len(cta) + 2 < self.config.max_length:
                caption = f"{caption}\n\n{cta}"
        
        # Platform-specific adjustments
        caption = self._adjust_for_platform(caption, platform)
        
        # Ensure within length limit
        if len(caption) > self.config.max_length:
            caption = caption[:self.config.max_length - 3] + "..."
        
        return caption.strip()
    
    def _detect_category(self, text: str) -> str:
        """Detect content category from text."""
        text = text.lower()
        
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score
        
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category
        
        return "general"
    
    def _clean_title(self, title: str) -> str:
        """Clean up title for caption use."""
        # Remove common filler words and clean up
        title = re.sub(r'\[.*?\]', '', title)  # Remove bracketed text
        title = re.sub(r'\(.*?\)', '', title)  # Remove parenthetical
        title = re.sub(r'#\w+', '', title)  # Remove hashtags
        title = re.sub(r'@\w+', '', title)  # Remove mentions
        title = re.sub(r'https?://\S+', '', title)  # Remove URLs
        title = ' '.join(title.split())  # Normalize whitespace
        
        # Capitalize properly
        if title:
            title = title.strip()
            if title and not title[0].isupper():
                title = title[0].upper() + title[1:]
        
        return title
    
    def _adjust_for_platform(self, caption: str, platform: str) -> str:
        """Adjust caption for specific platform."""
        if platform == "twitter":
            # Twitter has 280 char limit
            if len(caption) > 280:
                caption = caption[:277] + "..."
        elif platform == "instagram":
            # Instagram allows longer captions
            pass
        elif platform == "tiktok":
            # TikTok prefers shorter, punchy captions
            if len(caption) > 150:
                # Find a good break point
                parts = caption.split('\n')
                caption = parts[0]
        elif platform == "youtube":
            # YouTube Shorts description
            pass
        
        return caption
    
    def generate_variations(
        self,
        title: str = "",
        description: str = "",
        tags: List[str] = None,
        count: int = 3
    ) -> List[str]:
        """Generate multiple caption variations."""
        variations = []
        seen = set()
        
        # Generate unique variations
        max_attempts = count * 3
        attempts = 0
        
        while len(variations) < count and attempts < max_attempts:
            caption = self.generate_caption(title, description, tags)
            
            # Check for uniqueness
            caption_hash = caption[:50]  # Use first 50 chars as simple hash
            if caption_hash not in seen:
                variations.append(caption)
                seen.add(caption_hash)
            
            attempts += 1
        
        return variations
