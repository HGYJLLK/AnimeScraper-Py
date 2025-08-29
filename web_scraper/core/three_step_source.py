"""
Three Step Web Media Source - Python port of Kotlin ThreeStepWebMediaSource

Implements the three-step scraping pattern:
1. Search anime → find anime list
2. Get episodes lists → extract episode list for each anime  
3. Extract video URLs → get actual playable URLs
"""

import re
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Iterator
import requests
from bs4 import BeautifulSoup

from ..models import (
    Bangumi, Episode, MediaFetchRequest, MediaMatch, Media,
    EpisodeSort, EpisodeRange, MediaProperties, MediaSourceKind,
    MediaSourceLocation, SubtitleKind, FileSize, ResourceLocation,
    MatchKind
)


class ThreeStepWebMediaSource(ABC):
    """
    Abstract base class for three-step web media sources.
    
    Implements the pattern:
    1. Search anime by name → get anime list
    2. For each anime, get episode list 
    3. For each episode, extract video URL
    """
    
    def __init__(self, media_source_id: str, base_url: str, 
                 session: Optional[requests.Session] = None):
        self.media_source_id = media_source_id
        self.base_url = base_url.rstrip('/')
        self.session = session or requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.subtitle_languages = ["CHS"]
    
    @abstractmethod
    def parse_bangumi_search(self, document: BeautifulSoup) -> List[Bangumi]:
        """Parse search results to extract anime/bangumi list"""
        pass
    
    @abstractmethod
    async def search(self, name: str, query: MediaFetchRequest) -> List[Bangumi]:
        """Search for anime by name"""
        pass
    
    @abstractmethod
    def parse_episode_list(self, document: BeautifulSoup) -> List[Episode]:
        """Parse anime page to extract episode list"""
        pass
    
    def _is_possibly_movie(self, title: str) -> bool:
        """Check if the title might be a movie based on quality indicators"""
        return (("简" in title or "繁" in title) and 
                any(quality in title for quality in ["2160P", "1440P", "2K", "4K", "1080P", "720P"]))
    
    def _parse_episode_sort(self, name: str) -> EpisodeSort:
        """Parse episode number from episode name"""
        # Remove prefix "第" and suffix "集"
        clean_name = name.removeprefix("第").removesuffix("集")
        
        # Try to extract number
        match = re.search(r'\d+', clean_name)
        if match:
            return EpisodeSort(int(match.group()))
        
        return EpisodeSort(clean_name)
    
    def create_media_match(self, bangumi: Bangumi, episode: Episode) -> MediaMatch:
        """Create MediaMatch from bangumi and episode information"""
        sort = self._parse_episode_sort(episode.name)
        
        # Add channel suffix if present
        suffix_channel = f"-{episode.channel}" if episode.channel else ""
        
        # Handle movie special case
        if self._is_possibly_movie(episode.name) and isinstance(sort.value, str):
            episode_range = EpisodeRange.single(EpisodeSort(1))  # Movies are always episode 1
        else:
            episode_range = EpisodeRange.single(sort)
        
        media = Media(
            media_id=f"{self.media_source_id}.{bangumi.internal_id}-{sort}{suffix_channel}",
            media_source_id=self.media_source_id,
            original_url=bangumi.url,
            download=ResourceLocation.web_video(episode.url),
            original_title=f"{bangumi.name} {episode.name} {episode.channel or ''}".strip(),
            published_time=0,
            properties=MediaProperties(
                subject_name=bangumi.name,
                episode_name=episode.name,
                subtitle_language_ids=self.subtitle_languages,
                resolution="1080P",
                alliance=self.media_source_id,
                size=FileSize.unspecified(),
                subtitle_kind=SubtitleKind.EMBEDDED,
            ),
            episode_range=episode_range,
            location=MediaSourceLocation.ONLINE,
            kind=MediaSourceKind.WEB,
        )
        
        return MediaMatch(media, MatchKind.FUZZY)
    
    def check_connection(self) -> str:
        """Check connection to the base URL"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            return "SUCCESS" if response.status_code == 200 else "FAILED"
        except Exception as e:
            print(f"Connection check failed for {self.media_source_id}: {e}")
            return "FAILED"
    
    async def fetch(self, query: MediaFetchRequest) -> Iterator[MediaMatch]:
        """
        Main fetch method implementing the three-step pattern:
        1. Search each subject name → get bangumi list
        2. For each bangumi → get episode list
        3. For each episode → create media match
        """
        all_matches = []
        
        for subject_name in query.subject_names:
            try:
                # Step 1: Search for bangumi
                bangumi_list = await self._search_with_retry(subject_name, query)
                if not bangumi_list:
                    continue
                
                # Step 2: For each bangumi, get episodes
                for bangumi in bangumi_list:
                    try:
                        episodes = await self._get_episodes_with_retry(bangumi)
                        if not episodes:
                            continue
                        
                        # Step 3: Create media matches
                        for episode in episodes:
                            match = self.create_media_match(bangumi, episode)
                            
                            # Filter matches
                            if (match.definitely_matches(query) or 
                                self._is_possibly_movie(match.media.original_title)):
                                all_matches.append(match)
                        
                        print(f"{self.media_source_id} fetched {len(episodes)} episodes for '{subject_name}': "
                              f"{[ep.name for ep in episodes[:5]]}")  # Show first 5
                        
                    except Exception as e:
                        print(f"Error getting episodes for {bangumi.name}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error searching for '{subject_name}': {e}")
                continue
        
        return iter(all_matches)
    
    async def _search_with_retry(self, name: str, query: MediaFetchRequest, retries: int = 3) -> List[Bangumi]:
        """Search with retry logic"""
        for attempt in range(retries):
            try:
                return await self.search(name, query)
            except Exception as e:
                print(f"Search attempt {attempt + 1} failed for '{name}': {e}")
                if attempt < retries - 1:
                    await self._async_sleep(1.0)  # Wait before retry
                else:
                    return []
        return []
    
    async def _get_episodes_with_retry(self, bangumi: Bangumi, retries: int = 3) -> List[Episode]:
        """Get episodes with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(bangumi.url)
                response.raise_for_status()
                document = BeautifulSoup(response.text, 'html.parser')
                return self.parse_episode_list(document)
                
            except Exception as e:
                print(f"Episode fetch attempt {attempt + 1} failed for {bangumi.name}: {e}")
                if attempt < retries - 1:
                    await self._async_sleep(1.0)  # Wait before retry
                else:
                    return []
        return []
    
    async def _async_sleep(self, duration: float):
        """Async sleep helper"""
        import asyncio
        await asyncio.sleep(duration)


class SimpleThreeStepWebMediaSource(ThreeStepWebMediaSource):
    """
    Concrete implementation of ThreeStepWebMediaSource with configurable selectors.
    
    This provides a simple way to create a three-step scraper by just providing
    CSS selectors instead of implementing the abstract methods.
    """
    
    def __init__(self, media_source_id: str, base_url: str, 
                 search_config: dict, session: Optional[requests.Session] = None):
        super().__init__(media_source_id, base_url, session)
        self.search_config = search_config
    
    def parse_bangumi_search(self, document: BeautifulSoup) -> List[Bangumi]:
        """Parse search results using configured selectors"""
        bangumi_list = []
        config = self.search_config.get('bangumi', {})
        
        items = document.select(config.get('item_selector', '.search-item'))
        
        for i, item in enumerate(items):
            try:
                # Extract name
                name_elem = item.select_one(config.get('name_selector', '.title'))
                if not name_elem:
                    continue
                name = name_elem.get_text(strip=True)
                
                # Extract URL
                url_elem = item.select_one(config.get('url_selector', 'a'))
                if not url_elem or not url_elem.get('href'):
                    continue
                
                url = url_elem['href']
                if not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                
                # Generate internal ID
                internal_id = f"{i}_{hash(name) % 10000}"
                
                bangumi_list.append(Bangumi(
                    internal_id=internal_id,
                    name=name,
                    url=url
                ))
                
            except Exception as e:
                print(f"Error parsing bangumi item: {e}")
                continue
        
        return bangumi_list
    
    async def search(self, name: str, query: MediaFetchRequest) -> List[Bangumi]:
        """Search for anime using configured search URL and selectors"""
        config = self.search_config
        search_url = config.get('search_url', '').replace('{keyword}', name)
        
        if not search_url:
            return []
        
        try:
            response = self.session.get(search_url)
            response.raise_for_status()
            document = BeautifulSoup(response.text, 'html.parser')
            return self.parse_bangumi_search(document)
            
        except Exception as e:
            print(f"Search failed for '{name}': {e}")
            return []
    
    def parse_episode_list(self, document: BeautifulSoup) -> List[Episode]:
        """Parse episode list using configured selectors"""
        episodes = []
        config = self.search_config.get('episode', {})
        
        items = document.select(config.get('item_selector', '.episode-item'))
        
        for item in items:
            try:
                # Extract episode name
                name_elem = item.select_one(config.get('name_selector', '.episode-title'))
                if not name_elem:
                    continue
                name = name_elem.get_text(strip=True)
                
                # Extract episode URL
                url_elem = item.select_one(config.get('url_selector', 'a'))
                if not url_elem or not url_elem.get('href'):
                    continue
                
                url = url_elem['href']
                if not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                
                # Extract channel (optional)
                channel = None
                channel_selector = config.get('channel_selector')
                if channel_selector:
                    channel_elem = item.select_one(channel_selector)
                    if channel_elem:
                        channel = channel_elem.get_text(strip=True)
                
                episodes.append(Episode(
                    name=name,
                    url=url,
                    channel=channel
                ))
                
            except Exception as e:
                print(f"Error parsing episode item: {e}")
                continue
        
        return episodes