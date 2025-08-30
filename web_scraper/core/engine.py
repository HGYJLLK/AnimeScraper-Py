"""
Selector Media Source Engine - Python port of Kotlin SelectorMediaSourceEngine

Handles CSS selector-based parsing with three-phase flow:
1. Search subjects (anime series)
2. Parse subject pages for episodes
3. Extract video URLs from episodes
"""

import re
import time
from typing import List, Optional, Dict, Any, Sequence
from urllib.parse import urljoin, urlparse, quote_plus
import requests
from bs4 import BeautifulSoup, Tag
from pyquery import PyQuery as pq
from ..utils.logger import logger

from ..models import (
    WebSearchSubjectInfo, WebSearchEpisodeInfo, SelectorSearchQuery,
    Media, MediaProperties, EpisodeRange, EpisodeSort,
    MediaSourceKind, MediaSourceLocation, SubtitleKind, FileSize, ResourceLocation,
    SelectorSearchConfig
)


class SelectorMediaSourceEngine:
    """
    CSS Selector-based web scraping engine.
    
    Parsing flow:
    1. Search subject list: search_subjects()
    2. Parse subject page: select_subjects()
    3. Search episode list for a subject: search_episodes()
    4. Parse episode list page: select_episodes()
    5. Convert episode info to Media: select_media()
    """
    
    CURRENT_VERSION = 1
    DEFAULT_SUBTITLE_LANGUAGES = ["CHS"]
    
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._last_search_time = 0.0
    
    def _encode_url_segment(self, text: str) -> str:
        """URL encode a text segment"""
        return quote_plus(text)
    
    def _get_search_keyword(self, subject_name: str, remove_special: bool, use_only_first_word: bool) -> str:
        """Extract search keyword from subject name"""
        keyword = subject_name
        
        if remove_special:
            # Remove special characters
            keyword = re.sub(r'[^\w\s]', ' ', keyword)
        
        if use_only_first_word:
            keyword = keyword.split()[0] if keyword.split() else keyword
        
        return keyword.strip()
    
    async def _delay_until_next_allowed_search(self, interval_seconds: float):
        """Implement request rate limiting"""
        current_time = time.time()
        elapsed = current_time - self._last_search_time
        wait_time = interval_seconds - elapsed
        
        if wait_time > 0:
            time.sleep(wait_time)
        
        self._last_search_time = time.time()
    
    def search_subjects(self, search_url: str, subject_name: str, 
                       use_only_first_word: bool = True, 
                       remove_special: bool = True) -> tuple[str, Optional[BeautifulSoup]]:
        """
        Search for subjects based on given information.
        Returns (final_url, document) - document is None for 404
        """
        keyword = self._get_search_keyword(subject_name, remove_special, use_only_first_word)
        encoded_keyword = self._encode_url_segment(keyword)
        final_url = search_url.replace("{keyword}", encoded_keyword)
        
        try:
            response = self.session.get(final_url)
            if response.status_code == 404:
                return final_url, None
            
            response.raise_for_status()
            return final_url, BeautifulSoup(response.text, 'html.parser')
            
        except requests.RequestException as e:
            raise Exception(f"Failed to search subjects: {e}")
    
    def select_subjects(self, document: BeautifulSoup, config: SelectorSearchConfig) -> Optional[List[WebSearchSubjectInfo]]:
        """
        Parse subject search results. Returns all subjects on the page.
        Returns None if config is invalid.
        """
        if not config.subject_format_config.is_valid():
            return None
        
        try:
            # Use PyQuery for better CSS selector support
            doc = pq(str(document))
            subjects = []
            
            # Select subject elements
            subject_elements = doc(config.subject_format_config.subject_selector)
            
            for i, element in enumerate(subject_elements):
                el = pq(element)
                
                # Extract name
                name_el = el(config.subject_format_config.name_selector)
                if not name_el:
                    continue
                name = name_el.text().strip()
                if not name:
                    continue
                
                # Extract URL
                url_el = el(config.subject_format_config.url_selector)
                if not url_el:
                    continue
                
                partial_url = url_el.attr('href') or url_el.text().strip()
                if not partial_url:
                    continue
                
                # Make absolute URL
                full_url = urljoin(config.final_base_url, partial_url)
                
                # Generate internal ID
                internal_id = f"{i}_{hash(name) % 10000}"
                
                subjects.append(WebSearchSubjectInfo(
                    internal_id=internal_id,
                    name=name,
                    full_url=full_url,
                    partial_url=partial_url,
                    origin=element
                ))
            
            return subjects
            
        except Exception as e:
            logger.error(f"选择主题时出错: {e}")
            return []
    
    def search_episodes(self, subject_details_page_url: str) -> Optional[BeautifulSoup]:
        """
        Search episodes for a subject.
        Returns None for 404.
        """
        try:
            response = self.session.get(subject_details_page_url)
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
            
        except requests.RequestException as e:
            raise Exception(f"Failed to search episodes: {e}")
    
    def select_episodes(self, subject_details_page: BeautifulSoup, 
                       subject_url: str, config: SelectorSearchConfig) -> Optional[List[WebSearchEpisodeInfo]]:
        """
        Parse episode list from subject details page.
        Returns None if config is invalid.
        """
        if not config.channel_format_config.is_valid():
            return None
        
        try:
            # Calculate base URL for relative links
            parsed = urlparse(subject_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}{'/'.join(parsed.path.split('/')[:-1])}"
            
            doc = pq(str(subject_details_page))
            episodes = []
            
            # Select episode elements
            episode_elements = doc(config.channel_format_config.episode_selector)
            
            for element in episode_elements:
                el = pq(element)
                
                # Extract episode name
                name_el = el(config.channel_format_config.name_selector)
                if not name_el:
                    continue
                name = name_el.text().strip()
                if not name:
                    continue
                
                # Extract play URL
                url_el = el(config.channel_format_config.url_selector)
                if not url_el:
                    continue
                
                play_url = url_el.attr('href') or url_el.text().strip()
                if not play_url:
                    continue
                
                # Make absolute URL
                if not play_url.startswith(('http://', 'https://')):
                    play_url = urljoin(base_url, play_url)
                
                # Extract channel if configured
                channel = None
                if config.channel_format_config.channel_selector:
                    channel_el = el(config.channel_format_config.channel_selector)
                    if channel_el:
                        channel = channel_el.text().strip()
                
                # Parse episode sort
                episode_sort = self._parse_episode_sort(name)
                
                episodes.append(WebSearchEpisodeInfo(
                    channel=channel,
                    name=name,
                    episode_sort_or_ep=episode_sort,
                    play_url=play_url
                ))
            
            return episodes
            
        except Exception as e:
            logger.error(f"选择剧集时出错: {e}")
            return []
    
    def _parse_episode_sort(self, name: str) -> Optional[EpisodeSort]:
        """Parse episode sort from episode name"""
        # Try to extract episode number
        patterns = [
            r'第(\d+)集',  # 第1集
            r'第(\d+)话',  # 第1话
            r'EP(\d+)',   # EP01
            r'(\d+)集',   # 01集
            r'(\d+)话',   # 01话
            r'^(\d+)$',   # Just number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return EpisodeSort(int(match.group(1)))
        
        return None
    
    def select_media(self, episodes: Sequence[WebSearchEpisodeInfo], 
                    config: SelectorSearchConfig, query: SelectorSearchQuery,
                    media_source_id: str, subject_name: str) -> List[Media]:
        """
        Convert episode information to Media objects.
        """
        media_list = []
        
        for info in episodes:
            if info.episode_sort_or_ep is None:
                continue
            
            # Build media ID
            media_id_parts = [media_source_id]
            if config.select_media.distinguish_subject_name:
                media_id_parts.extend([subject_name, "-"])
            if config.select_media.distinguish_channel_name and info.channel:
                media_id_parts.extend([info.channel, "-"])
            media_id_parts.extend([info.name, "-", str(info.episode_sort_or_ep)])
            
            media_id = "".join(media_id_parts)
            
            # Build original title
            title_parts = []
            if config.select_media.distinguish_subject_name:
                title_parts.append(subject_name)
            title_parts.append(info.name)
            original_title = " ".join(title_parts)
            
            # Guess subtitle languages
            subtitle_languages = self._guess_subtitle_languages(info)
            
            media = Media(
                media_id=media_id,
                media_source_id=media_source_id,
                original_url=info.play_url,
                download=ResourceLocation.web_video(info.play_url),
                original_title=original_title,
                published_time=0,
                properties=MediaProperties(
                    subject_name=subject_name,
                    episode_name=info.name,
                    subtitle_language_ids=subtitle_languages or [config.default_subtitle_language],
                    resolution=config.default_resolution,
                    alliance=info.channel or "",
                    size=FileSize.unspecified(),
                    subtitle_kind=SubtitleKind.EMBEDDED,
                ),
                episode_range=EpisodeRange.single(info.episode_sort_or_ep),
                location=MediaSourceLocation.ONLINE,
                kind=MediaSourceKind.WEB,
            )
            
            media_list.append(media)
        
        return media_list
    
    def _guess_subtitle_languages(self, info: WebSearchEpisodeInfo) -> Optional[List[str]]:
        """Guess subtitle languages from channel and episode name"""
        languages = []
        
        # Check channel name
        if info.channel:
            if "简" in info.channel or "简中" in info.channel:
                languages.append("CHS")
            elif "繁" in info.channel or "繁中" in info.channel:
                languages.append("CHT")
        
        # Check episode name
        if "简" in info.name or "简中" in info.name:
            languages.append("CHS")
        elif "繁" in info.name or "繁中" in info.name:
            languages.append("CHT")
        
        return languages if languages else None
    
    def should_load_page(self, url: str, config) -> bool:
        """Check if page should be loaded for nested URL extraction"""
        if config.enable_nested_url and config.match_nested_url_regex:
            return bool(config.match_nested_url_regex.search(url))
        return False
    
    def match_web_video(self, url: str, config) -> Dict[str, Any]:
        """Match web video URL and extract video information"""
        if self.should_load_page(url, config):
            return {"action": "load_page"}
        
        if config.match_video_url_regex:
            match = config.match_video_url_regex.search(url)
            if match:
                # Try to extract video URL from named group 'v'
                try:
                    video_url = match.group('v') if 'v' in match.groupdict() else url
                except IndexError:
                    video_url = url
                
                return {
                    "action": "matched",
                    "video_url": video_url,
                    "headers": {
                        "User-Agent": config.add_headers_to_video.user_agent,
                        "Referer": config.add_headers_to_video.referer,
                        "Sec-Ch-Ua-Mobile": "?0",
                        "Sec-Ch-Ua-Platform": "macOS",
                        "Sec-Fetch-Dest": "video",
                        "Sec-Fetch-Mode": "no-cors",
                        "Sec-Fetch-Site": "cross-site",
                    }
                }
        
        return {"action": "continue"}