"""
Media models for web scraper - Python port of Kotlin media classes
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import re


class EpisodeSort:
    """Episode sort representation"""
    
    def __init__(self, value):
        if isinstance(value, str):
            # Try to extract number from string
            match = re.search(r'\d+', value)
            if match:
                self.value = int(match.group())
            else:
                self.value = value
        else:
            self.value = value
    
    def __str__(self):
        return str(self.value)
    
    def __eq__(self, other):
        if isinstance(other, EpisodeSort):
            return self.value == other.value
        return False


class EpisodeRange:
    """Episode range representation"""
    
    def __init__(self, start: EpisodeSort, end: Optional[EpisodeSort] = None):
        self.start = start
        self.end = end or start
    
    @classmethod
    def single(cls, episode_sort: EpisodeSort):
        """Create a single episode range"""
        return cls(episode_sort)
    
    def __str__(self):
        if self.start == self.end:
            return str(self.start)
        return f"{self.start}-{self.end}"


class MediaSourceKind(Enum):
    WEB = "WEB"
    TORRENT = "TORRENT"


class MediaSourceLocation(Enum):
    ONLINE = "ONLINE"
    LOCAL = "LOCAL"


class SubtitleKind(Enum):
    EMBEDDED = "EMBEDDED"
    EXTERNAL = "EXTERNAL"


@dataclass
class FileSize:
    """File size representation"""
    bytes: int
    
    @classmethod
    def unspecified(cls):
        return cls(bytes=0)
    
    def __str__(self):
        if self.bytes == 0:
            return "Unspecified"
        # Convert to human readable format
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.bytes < 1024.0:
                return f"{self.bytes:.1f}{unit}"
            self.bytes /= 1024.0
        return f"{self.bytes:.1f}PB"


@dataclass
class ResourceLocation:
    """Resource location for downloads"""
    url: str
    
    @classmethod
    def web_video(cls, url: str):
        return cls(url=url)


@dataclass
class MediaProperties:
    """Media properties"""
    subject_name: str
    episode_name: str
    subtitle_language_ids: List[str] = field(default_factory=lambda: ["CHS"])
    resolution: str = "1080P"
    alliance: str = ""
    size: FileSize = field(default_factory=FileSize.unspecified)
    subtitle_kind: SubtitleKind = SubtitleKind.EMBEDDED


@dataclass
class Media:
    """Base media representation"""
    media_id: str
    media_source_id: str
    original_url: str
    download: ResourceLocation
    original_title: str
    published_time: int
    properties: MediaProperties
    episode_range: EpisodeRange
    location: MediaSourceLocation
    kind: MediaSourceKind


class MatchKind(Enum):
    EXACT = "EXACT"
    FUZZY = "FUZZY"


@dataclass
class MediaMatch:
    """Media match result"""
    media: Media
    match_kind: MatchKind
    
    def definitely_matches(self, query) -> bool:
        """Check if this match definitely matches the query"""
        # Simple implementation - can be enhanced
        return True


@dataclass
class MediaFetchRequest:
    """Request for fetching media"""
    subject_names: List[str]
    episode_sort: Optional[EpisodeSort] = None
    episode_ep: Optional[EpisodeSort] = None
    episode_name: Optional[str] = None