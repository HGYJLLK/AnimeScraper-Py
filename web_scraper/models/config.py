"""
Configuration models for web scraper - Python port of Kotlin config classes
"""

from dataclasses import dataclass, field
from typing import List, Optional
import re


@dataclass
class VideoHeaders:
    """Video request headers configuration"""
    referer: str = ""
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"


@dataclass
class MatchVideoConfig:
    """Video matching configuration"""
    enable_nested_url: bool = True
    match_nested_url: str = r"^.+(m3u8|vip|xigua\.php).+\?"
    match_video_url: str = r"(^http(s)?:\/\/(?!.*http(s)?:\/\/).+((\.mp4)|(\.mkv)|(m3u8)).*(\?.+)?)|(akamaized)|(bilivideo.com)"
    cookies: str = "quality=1080"
    add_headers_to_video: VideoHeaders = field(default_factory=VideoHeaders)
    
    @property
    def match_nested_url_regex(self) -> Optional[re.Pattern]:
        """Get compiled regex for nested URL matching"""
        try:
            return re.compile(self.match_nested_url)
        except re.error:
            return None
    
    @property
    def match_video_url_regex(self) -> Optional[re.Pattern]:
        """Get compiled regex for video URL matching"""
        try:
            return re.compile(self.match_video_url)
        except re.error:
            return None


@dataclass
class SelectMediaConfig:
    """Media selection configuration"""
    distinguish_subject_name: bool = True
    distinguish_channel_name: bool = True


@dataclass
class SelectorFormatConfig:
    """Base selector format configuration"""
    
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return True


@dataclass
class SelectorSubjectFormatConfig(SelectorFormatConfig):
    """Subject format configuration for CSS selectors"""
    subject_selector: str = ""
    name_selector: str = ""
    url_selector: str = ""
    
    def is_valid(self) -> bool:
        return bool(self.subject_selector and self.name_selector and self.url_selector)


@dataclass 
class SelectorChannelFormatConfig(SelectorFormatConfig):
    """Channel format configuration for CSS selectors"""
    episode_selector: str = ""
    name_selector: str = ""
    url_selector: str = ""
    channel_selector: str = ""
    
    def is_valid(self) -> bool:
        return bool(self.episode_selector and self.name_selector and self.url_selector)


@dataclass
class SelectorSearchConfig:
    """Main search configuration - Python port of Kotlin SelectorSearchConfig"""
    
    # Phase 1: Search
    search_url: str = ""
    search_use_only_first_word: bool = True
    search_remove_special: bool = True
    search_use_subject_names_count: int = 1
    raw_base_url: str = ""
    request_interval_seconds: float = 3.0
    
    # Phase 2: Subject selection
    subject_format_id: str = "subject_format_a"
    subject_format_config: SelectorSubjectFormatConfig = field(default_factory=SelectorSubjectFormatConfig)
    
    # Phase 3: Channel/Episode selection
    channel_format_id: str = "channel_format_no_channel"
    channel_format_config: SelectorChannelFormatConfig = field(default_factory=SelectorChannelFormatConfig)
    
    # Media properties
    default_resolution: str = "1080P"
    default_subtitle_language: str = "CHS"
    only_supports_players: List[str] = field(default_factory=list)
    
    # Filtering
    filter_by_episode_sort: bool = True
    filter_by_subject_name: bool = True
    
    # Media selection and video matching
    select_media: SelectMediaConfig = field(default_factory=SelectMediaConfig)
    match_video: MatchVideoConfig = field(default_factory=MatchVideoConfig)
    
    @property
    def final_base_url(self) -> str:
        """Get final base URL, guessing if not provided"""
        if self.raw_base_url:
            return self.raw_base_url
        return self._guess_base_url(self.search_url)
    
    @staticmethod
    def _guess_base_url(search_url: str) -> str:
        """Guess base URL from search URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(search_url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            # Fallback to simple string manipulation
            schema_index = search_url.find("//")
            if schema_index == -1:
                return search_url.rstrip("/")
            else:
                slash_index = search_url.find("/", schema_index + 2)
                if slash_index == -1:
                    return search_url.rstrip("/")
                else:
                    return search_url[:slash_index]