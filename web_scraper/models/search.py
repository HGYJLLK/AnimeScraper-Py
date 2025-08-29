"""
Search models for web scraper - Python port of Kotlin search classes
"""

from dataclasses import dataclass
from typing import Optional, Set
from .media import EpisodeSort


@dataclass
class WebSearchSubjectInfo:
    """Search result for a subject/anime"""
    internal_id: str
    name: str
    full_url: str
    partial_url: str
    origin: Optional[object] = None  # HTML element


@dataclass
class WebSearchChannelInfo:
    """Channel information for episodes"""
    name: str
    content: object  # HTML element


@dataclass
class WebSearchEpisodeInfo:
    """Episode information from search"""
    channel: Optional[str]
    name: str
    episode_sort_or_ep: Optional[EpisodeSort]
    play_url: str


@dataclass
class SelectorSearchQuery:
    """Query for selector-based search"""
    subject_name: str
    all_subject_names: Set[str]
    episode_sort: EpisodeSort
    episode_ep: Optional[EpisodeSort]
    episode_name: Optional[str]


@dataclass
class Bangumi:
    """Bangumi/anime series information"""
    internal_id: str
    name: str
    url: str


@dataclass
class Episode:
    """Episode information"""
    name: str
    url: str
    channel: Optional[str] = None