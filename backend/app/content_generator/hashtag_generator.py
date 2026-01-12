"""
Hashtag generator for social media posts.
Uses keyword extraction and trending templates - no paid APIs needed.
"""
import re
from typing import List, Set
from dataclasses import dataclass
import random


@dataclass
class HashtagConfig:
    """Configuration for hashtag generation."""
    max_hashtags: int = 10
    include_trending: bool = True
    include_niche: bool = True


class HashtagGenerator:
    """
    Generates relevant hashtags for video clips.
    Template-based approach - no external API dependencies.
    """
    
    # Popular general hashtags
    GENERAL_HASHTAGS = [
        "fyp", "foryou", "viral", "trending", "explore",
        "content", "video", "clip", "moment", "mustwatch"
    ]
    
    # Category-specific hashtags
    CATEGORY_HASHTAGS = {
        "gaming": [
            "gaming", "gamer", "gamingcommunity", "videogames", "gaminglife",
            "esports", "twitch", "streamer", "gameplay", "gamingclips",
            "pcgaming", "consolegaming", "gamingmoments", "epicmoment", "clutch"
        ],
        "sports": [
            "sports", "athlete", "fitness", "workout", "training",
            "highlights", "sportshighlights", "amazing", "incredible", "bestplay",
            "sportsclip", "gameday", "champion", "winner", "goat"
        ],
        "music": [
            "music", "musician", "newmusic", "song", "artist",
            "musicvideo", "live", "performance", "concert", "vibes",
            "musiclover", "goodmusic", "musiclife", "beats", "sound"
        ],
        "comedy": [
            "comedy", "funny", "humor", "laugh", "lol",
            "memes", "funnyvideos", "comedyclub", "jokes", "hilarious",
            "trynottolaugh", "comedygold", "laughing", "funnymoments", "humor"
        ],
        "educational": [
            "education", "learn", "learning", "knowledge", "facts",
            "didyouknow", "tutorial", "howto", "tips", "educational",
            "learnontiktok", "edutok", "science", "study", "interesting"
        ],
        "motivational": [
            "motivation", "inspiration", "success", "mindset", "goals",
            "entrepreneur", "hustle", "grind", "nevergiveup", "motivated",
            "successmindset", "inspire", "motivational", "growth", "achieve"
        ],
        "lifestyle": [
            "lifestyle", "life", "daily", "routine", "vlog",
            "dayinmylife", "aesthetic", "vibes", "mood", "livingmybestlife"
        ],
        "food": [
            "food", "foodie", "cooking", "recipe", "delicious",
            "yummy", "foodporn", "homemade", "chef", "foodlover"
        ],
        "travel": [
            "travel", "adventure", "explore", "wanderlust", "trip",
            "vacation", "tourist", "traveler", "travelgram", "discover"
        ],
        "beauty": [
            "beauty", "makeup", "skincare", "beautytips", "glam",
            "beautyhacks", "makeuptutorial", "skincareroutine", "glow", "selfcare"
        ]
    }
    
    # Platform-specific trending hashtags
    PLATFORM_HASHTAGS = {
        "tiktok": ["fyp", "foryou", "foryoupage", "viral", "tiktok", "trending", "xyzbca"],
        "instagram": ["reels", "reelsinstagram", "instareels", "explore", "instagood", "instagram"],
        "youtube": ["shorts", "youtubeshorts", "subscribe", "viral", "trending", "youtube"],
        "twitter": ["viral", "trending", "thread", "mustwatch", "video"]
    }
    
    # Keywords that map to categories
    CATEGORY_KEYWORDS = {
        "gaming": ["game", "play", "stream", "xbox", "playstation", "pc", "gamer", "esport"],
        "sports": ["sport", "football", "basketball", "soccer", "tennis", "golf", "athlete", "workout", "fitness"],
        "music": ["music", "song", "artist", "singer", "band", "concert", "dj", "beat"],
        "comedy": ["funny", "comedy", "laugh", "joke", "humor", "meme", "prank"],
        "educational": ["learn", "education", "tutorial", "how to", "explain", "science", "tip"],
        "motivational": ["motivat", "inspir", "success", "goal", "dream", "mindset"],
        "lifestyle": ["life", "daily", "routine", "vlog", "day"],
        "food": ["food", "cook", "recipe", "eat", "restaurant", "chef"],
        "travel": ["travel", "trip", "vacation", "adventure", "explore", "visit"],
        "beauty": ["makeup", "beauty", "skincare", "hair", "glam", "fashion"]
    }
    
    def __init__(self, config: HashtagConfig = None):
        self.config = config or HashtagConfig()
    
    def generate_hashtags(
        self,
        title: str = "",
        description: str = "",
        tags: List[str] = None,
        platform: str = "general",
        custom_hashtags: List[str] = None
    ) -> List[str]:
        """
        Generate hashtags based on video metadata.
        
        Args:
            title: Video title
            description: Video description
            tags: Video tags
            platform: Target platform
            custom_hashtags: User-provided custom hashtags
            
        Returns:
            List of hashtags (without # prefix)
        """
        tags = tags or []
        custom_hashtags = custom_hashtags or []
        
        hashtags: Set[str] = set()
        
        # Add custom hashtags first
        for tag in custom_hashtags:
            clean = self._clean_hashtag(tag)
            if clean:
                hashtags.add(clean)
        
        # Extract keywords and detect category
        all_text = f"{title} {description} {' '.join(tags)}".lower()
        categories = self._detect_categories(all_text)
        
        # Add category-specific hashtags
        for category in categories[:2]:  # Top 2 categories
            category_tags = self.CATEGORY_HASHTAGS.get(category, [])
            for tag in random.sample(category_tags, min(4, len(category_tags))):
                hashtags.add(tag)
        
        # Add platform-specific hashtags
        if platform in self.PLATFORM_HASHTAGS:
            platform_tags = self.PLATFORM_HASHTAGS[platform]
            for tag in random.sample(platform_tags, min(3, len(platform_tags))):
                hashtags.add(tag)
        
        # Add general trending hashtags
        if self.config.include_trending:
            for tag in random.sample(self.GENERAL_HASHTAGS, min(3, len(self.GENERAL_HASHTAGS))):
                hashtags.add(tag)
        
        # Extract keywords from title/description
        keywords = self._extract_keywords(title, description)
        for kw in keywords[:5]:
            hashtags.add(kw)
        
        # Convert tags to hashtags
        for tag in tags[:3]:
            clean = self._clean_hashtag(tag)
            if clean:
                hashtags.add(clean)
        
        # Limit to max hashtags
        hashtag_list = list(hashtags)[:self.config.max_hashtags]
        
        return hashtag_list
    
    def _clean_hashtag(self, tag: str) -> str:
        """Clean and format a hashtag."""
        # Remove # prefix if present
        tag = tag.lstrip('#')
        
        # Remove non-alphanumeric characters (except underscores)
        tag = re.sub(r'[^\w]', '', tag)
        
        # Convert to lowercase
        tag = tag.lower()
        
        # Remove leading numbers
        tag = re.sub(r'^\d+', '', tag)
        
        return tag if len(tag) >= 2 else ""
    
    def _detect_categories(self, text: str) -> List[str]:
        """Detect content categories from text."""
        scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score
        
        # Sort by score descending
        sorted_categories = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        return sorted_categories if sorted_categories else ["general"]
    
    def _extract_keywords(self, title: str, description: str) -> List[str]:
        """Extract potential hashtag keywords from text."""
        text = f"{title} {description}".lower()
        
        # Remove URLs, mentions, existing hashtags
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,15}\b', text)
        
        # Filter out common words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'will',
            'with', 'this', 'that', 'from', 'they', 'what', 'which', 'when',
            'where', 'who', 'how', 'than', 'then', 'just', 'only', 'also',
            'very', 'much', 'more', 'most', 'some', 'such', 'into', 'over',
            'after', 'before', 'about', 'because', 'being', 'between'
        }
        
        keywords = [w for w in words if w not in stop_words]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords
    
    def format_hashtags(
        self, 
        hashtags: List[str], 
        style: str = "inline"
    ) -> str:
        """
        Format hashtags for display.
        
        Args:
            hashtags: List of hashtags (without #)
            style: Format style (inline, block, spaced)
            
        Returns:
            Formatted hashtag string
        """
        if not hashtags:
            return ""
        
        prefixed = [f"#{tag}" for tag in hashtags]
        
        if style == "inline":
            return " ".join(prefixed)
        elif style == "block":
            return "\n".join(prefixed)
        elif style == "spaced":
            return "  ".join(prefixed)
        else:
            return " ".join(prefixed)
    
    def generate_for_all_platforms(
        self,
        title: str = "",
        description: str = "",
        tags: List[str] = None
    ) -> dict:
        """Generate platform-specific hashtags."""
        platforms = ["tiktok", "instagram", "youtube", "twitter"]
        
        result = {}
        for platform in platforms:
            result[platform] = self.generate_hashtags(
                title=title,
                description=description,
                tags=tags,
                platform=platform
            )
        
        return result
