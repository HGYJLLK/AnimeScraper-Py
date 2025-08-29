"""
Selector Media Source - Python port of Kotlin SelectorMediaSource

Main media source class that orchestrates the CSS selector-based scraping process.
"""

import time
import asyncio
from typing import List, Optional, Iterator, Dict, Any
import requests

from ..models import (
    SelectorSearchConfig, MediaFetchRequest, MediaMatch, Media,
    SelectorSearchQuery, EpisodeSort, MatchKind
)
from .engine import SelectorMediaSourceEngine


class ConnectionStatus:
    """Connection status enumeration"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class SelectorMediaSource:
    """
    Main selector-based media source implementation.
    
    Provides CSS selector-based web scraping functionality with:
    - Configurable search and parsing rules
    - Rate limiting
    - Three-phase scraping (search -> subjects -> episodes)
    - Video URL extraction and matching
    """
    
    FACTORY_ID = "web-selector"
    
    def __init__(self, media_source_id: str, config: SelectorSearchConfig, 
                 session: Optional[requests.Session] = None):
        self.media_source_id = media_source_id
        self.config = config
        self.engine = SelectorMediaSourceEngine(session)
        self._last_search_time = 0.0
    
    @property
    def info(self) -> Dict[str, Any]:
        """Get media source information"""
        return {
            "display_name": f"Selector-{self.media_source_id}",
            "description": "通用 CSS Selector 数据源",
            "website_url": self.config.search_url,
            "icon_url": "",
        }
    
    def check_connection(self) -> str:
        """Check connection to the media source"""
        try:
            response = requests.get(self.config.search_url, timeout=10)
            if response.status_code in [200, 401, 403]:  # Any non-network error is OK
                return ConnectionStatus.SUCCESS
            return ConnectionStatus.FAILED
        except requests.RequestException:
            return ConnectionStatus.FAILED
    
    async def _delay_until_next_allowed_search(self):
        """Implement request rate limiting"""
        current_time = time.time()
        elapsed = current_time - self._last_search_time
        wait_time = self.config.request_interval_seconds - elapsed
        
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        
        self._last_search_time = time.time()
    
    def _check_player_support(self) -> bool:
        """Check if current platform player is supported"""
        if not self.config.only_supports_players:
            return True
        
        # Simple platform detection - can be enhanced
        import platform
        system = platform.system().lower()
        
        current_player = "vlc"  # Default to VLC for desktop
        if system == "darwin":  # macOS
            current_player = "avkit"
        elif "android" in system:
            current_player = "exoplayer"
        
        return current_player in self.config.only_supports_players
    
    async def search(self, search_config: SelectorSearchConfig, query: SelectorSearchQuery) -> List[Media]:
        """
        Perform complete search operation: search subjects -> get episodes -> extract media
        """
        await self._delay_until_next_allowed_search()
        
        if not self._check_player_support():
            print(f"Player not supported. Supported: {self.config.only_supports_players}")
            return []
        
        try:
            # Phase 1: Search subjects
            search_url, document = self.engine.search_subjects(
                search_config.search_url,
                subject_name=query.subject_name,
                use_only_first_word=search_config.search_use_only_first_word,
                remove_special=search_config.search_remove_special,
            )
            
            if document is None:
                return []
            
            # Phase 2: Select subjects from search results
            subjects = self.engine.select_subjects(document, search_config)
            if not subjects:
                return []
            
            all_media = []
            
            # Phase 3: For each subject, get episodes and extract media
            for subject_info in subjects:
                try:
                    # Get episode document
                    episode_document = self.engine.search_episodes(subject_info.full_url)
                    if episode_document is None:
                        continue
                    
                    # Extract episodes
                    episodes = self.engine.select_episodes(
                        episode_document, subject_info.full_url, search_config
                    )
                    if not episodes:
                        continue
                    
                    # Convert to media objects
                    media_list = self.engine.select_media(
                        episodes, search_config, query, 
                        self.media_source_id, subject_info.name
                    )
                    
                    all_media.extend(media_list)
                    
                except Exception as e:
                    print(f"Error processing subject {subject_info.name}: {e}")
                    continue
            
            return all_media
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def fetch(self, query: MediaFetchRequest) -> Iterator[MediaMatch]:
        """
        Fetch media matches for the given query.
        Uses asyncio for the search but provides synchronous interface.
        """
        async def _async_fetch():
            all_matches = []
            
            # Process each subject name (limited by config)
            subject_names = query.subject_names[:self.config.search_use_subject_names_count]
            
            for subject_name in subject_names:
                search_query = SelectorSearchQuery(
                    subject_name=subject_name,
                    all_subject_names=set(query.subject_names),
                    episode_sort=query.episode_sort or EpisodeSort("1"),
                    episode_ep=query.episode_ep,
                    episode_name=query.episode_name,
                )
                
                media_list = await self.search(self.config, search_query)
                
                # Convert to MediaMatch objects
                for media in media_list:
                    all_matches.append(MediaMatch(media, MatchKind.FUZZY))
                
                # Add delay between different subject searches
                if len(subject_names) > 1:
                    await asyncio.sleep(self.config.request_interval_seconds)
            
            return all_matches
        
        # Run async function - handle existing event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, create a new thread to run the async code
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _async_fetch())
                matches = future.result()
        except RuntimeError:
            # No running event loop, safe to use asyncio.run
            matches = asyncio.run(_async_fetch())
        
        return iter(matches)
    
    def match_web_video(self, url: str) -> Dict[str, Any]:
        """Match and extract video information from URL"""
        return self.engine.match_web_video(url, self.config.match_video)


class SelectorMediaSourceFactory:
    """Factory for creating SelectorMediaSource instances"""
    
    FACTORY_ID = SelectorMediaSource.FACTORY_ID
    
    @property
    def info(self):
        return {
            "display_name": "Selector",
            "description": "通用 CSS Selector 数据源",
            "icon_url": "",
        }
    
    @property
    def allow_multiple_instances(self) -> bool:
        return True
    
    def create(self, media_source_id: str, config: SelectorSearchConfig, 
               session: Optional[requests.Session] = None) -> SelectorMediaSource:
        """Create a new SelectorMediaSource instance"""
        return SelectorMediaSource(media_source_id, config, session)