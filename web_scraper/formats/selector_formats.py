"""
Selector format implementations for different website structures.

This module provides format handlers for different types of website layouts:
- Subject formats: Handle search result pages with anime/subject listings
- Channel formats: Handle episode listing pages within subjects
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq
from urllib.parse import urljoin

from ..models import WebSearchSubjectInfo, WebSearchEpisodeInfo, EpisodeSort
from ..utils import parse_episode_number


class SelectorFormatId:
    """Format ID constants"""
    SUBJECT_FORMAT_A = "subject_format_a"
    SUBJECT_FORMAT_INDEXED = "subject_format_indexed" 
    CHANNEL_FORMAT_NO_CHANNEL = "channel_format_no_channel"
    CHANNEL_FORMAT_INDEX_GROUPED = "channel_format_index_grouped"


class SelectorFormat(ABC):
    """Base class for selector formats"""
    
    @property
    @abstractmethod
    def format_id(self) -> str:
        """Unique format identifier"""
        pass
    
    @abstractmethod
    def is_valid_config(self, config: Dict[str, Any]) -> bool:
        """Check if the provided configuration is valid for this format"""
        pass


class SelectorSubjectFormat(SelectorFormat):
    """Base class for subject selection formats"""
    
    @abstractmethod
    def select(self, document: BeautifulSoup, base_url: str, config: Dict[str, Any]) -> List[WebSearchSubjectInfo]:
        """Select subjects from search results page"""
        pass


class SelectorChannelFormat(SelectorFormat):
    """Base class for channel/episode selection formats"""
    
    @abstractmethod
    def select(self, document: BeautifulSoup, base_url: str, config: Dict[str, Any]) -> List[WebSearchEpisodeInfo]:
        """Select episodes from subject details page"""
        pass


class SelectorSubjectFormatA(SelectorSubjectFormat):
    """
    Subject format A: Standard CSS selector-based subject extraction.
    
    Configuration keys:
    - subject_selector: CSS selector for subject container elements
    - name_selector: CSS selector for subject name within each container
    - url_selector: CSS selector for subject URL within each container
    """
    
    format_id = SelectorFormatId.SUBJECT_FORMAT_A
    
    def is_valid_config(self, config: Dict[str, Any]) -> bool:
        required_keys = ['subject_selector', 'name_selector', 'url_selector']
        return all(config.get(key) for key in required_keys)
    
    def select(self, document: BeautifulSoup, base_url: str, config: Dict[str, Any]) -> List[WebSearchSubjectInfo]:
        if not self.is_valid_config(config):
            return []
        
        try:
            doc = pq(str(document))
            subjects = []
            
            subject_elements = doc(config['subject_selector'])
            
            for i, element in enumerate(subject_elements):
                el = pq(element)
                
                # Extract name
                name_el = el(config['name_selector'])
                if not name_el:
                    continue
                name = name_el.text().strip()
                if not name:
                    continue
                
                # Extract URL
                url_el = el(config['url_selector'])
                if not url_el:
                    continue
                
                partial_url = url_el.attr('href') or url_el.text().strip()
                if not partial_url:
                    continue
                
                # Make absolute URL
                full_url = urljoin(base_url, partial_url)
                
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
            print(f"Error in SelectorSubjectFormatA.select: {e}")
            return []


class SelectorSubjectFormatIndexed(SelectorSubjectFormat):
    """
    Subject format for indexed/numbered subject listings.
    
    Configuration keys:
    - container_selector: CSS selector for the main container
    - item_selector: CSS selector for each subject item
    - name_attr: Attribute name containing subject name (default: 'title')
    - url_attr: Attribute name containing URL (default: 'href')
    - index_attr: Attribute for indexing (optional)
    """
    
    format_id = SelectorFormatId.SUBJECT_FORMAT_INDEXED
    
    def is_valid_config(self, config: Dict[str, Any]) -> bool:
        required_keys = ['container_selector', 'item_selector']
        return all(config.get(key) for key in required_keys)
    
    def select(self, document: BeautifulSoup, base_url: str, config: Dict[str, Any]) -> List[WebSearchSubjectInfo]:
        if not self.is_valid_config(config):
            return []
        
        try:
            doc = pq(str(document))
            subjects = []
            
            # Find container first
            container = doc(config['container_selector']).first()
            if not container:
                return []
            
            # Find items within container
            items = container.find(config['item_selector'])
            
            name_attr = config.get('name_attr', 'title')
            url_attr = config.get('url_attr', 'href')
            
            for i, item in enumerate(items):
                el = pq(item)
                
                # Extract name from attribute or text
                name = el.attr(name_attr) or el.text().strip()
                if not name:
                    continue
                
                # Extract URL from attribute
                partial_url = el.attr(url_attr)
                if not partial_url:
                    continue
                
                full_url = urljoin(base_url, partial_url)
                internal_id = f"idx_{i}_{hash(name) % 10000}"
                
                subjects.append(WebSearchSubjectInfo(
                    internal_id=internal_id,
                    name=name,
                    full_url=full_url,
                    partial_url=partial_url,
                    origin=item
                ))
            
            return subjects
            
        except Exception as e:
            print(f"Error in SelectorSubjectFormatIndexed.select: {e}")
            return []


class SelectorChannelFormatNoChannel(SelectorChannelFormat):
    """
    Channel format for sites without channel concept - direct episode listing.
    
    Configuration keys:
    - episode_selector: CSS selector for episode elements
    - name_selector: CSS selector for episode name within each element
    - url_selector: CSS selector for episode URL within each element
    """
    
    format_id = SelectorFormatId.CHANNEL_FORMAT_NO_CHANNEL
    
    def is_valid_config(self, config: Dict[str, Any]) -> bool:
        required_keys = ['episode_selector', 'name_selector', 'url_selector']
        return all(config.get(key) for key in required_keys)
    
    def select(self, document: BeautifulSoup, base_url: str, config: Dict[str, Any]) -> List[WebSearchEpisodeInfo]:
        if not self.is_valid_config(config):
            return []
        
        try:
            doc = pq(str(document))
            episodes = []
            
            episode_elements = doc(config['episode_selector'])
            
            for element in episode_elements:
                el = pq(element)
                
                # Extract episode name
                name_el = el(config['name_selector'])
                if not name_el:
                    continue
                name = name_el.text().strip()
                if not name:
                    continue
                
                # Extract URL
                url_el = el(config['url_selector'])
                if not url_el:
                    continue
                
                partial_url = url_el.attr('href') or url_el.text().strip()
                if not partial_url:
                    continue
                
                full_url = urljoin(base_url, partial_url)
                
                # Parse episode sort
                episode_number = parse_episode_number(name)
                episode_sort = EpisodeSort(episode_number) if episode_number else None
                
                episodes.append(WebSearchEpisodeInfo(
                    channel=None,  # No channel concept in this format
                    name=name,
                    episode_sort_or_ep=episode_sort,
                    play_url=full_url
                ))
            
            return episodes
            
        except Exception as e:
            print(f"Error in SelectorChannelFormatNoChannel.select: {e}")
            return []


class SelectorChannelFormatIndexGrouped(SelectorChannelFormat):
    """
    Channel format for sites with grouped episodes by channel/source.
    
    Configuration keys:
    - channel_selector: CSS selector for channel containers
    - channel_name_selector: CSS selector for channel name within each container
    - episode_selector: CSS selector for episodes within each channel
    - episode_name_selector: CSS selector for episode name
    - episode_url_selector: CSS selector for episode URL
    """
    
    format_id = SelectorFormatId.CHANNEL_FORMAT_INDEX_GROUPED
    
    def is_valid_config(self, config: Dict[str, Any]) -> bool:
        required_keys = [
            'channel_selector', 'episode_selector', 
            'episode_name_selector', 'episode_url_selector'
        ]
        return all(config.get(key) for key in required_keys)
    
    def select(self, document: BeautifulSoup, base_url: str, config: Dict[str, Any]) -> List[WebSearchEpisodeInfo]:
        if not self.is_valid_config(config):
            return []
        
        try:
            doc = pq(str(document))
            episodes = []
            
            # Find channel containers
            channels = doc(config['channel_selector'])
            
            for channel_element in channels:
                channel_el = pq(channel_element)
                
                # Extract channel name
                channel_name = None
                if config.get('channel_name_selector'):
                    channel_name_el = channel_el(config['channel_name_selector'])
                    if channel_name_el:
                        channel_name = channel_name_el.text().strip()
                
                # Find episodes within this channel
                episode_elements = channel_el(config['episode_selector'])
                
                for episode_element in episode_elements:
                    ep_el = pq(episode_element)
                    
                    # Extract episode name
                    name_el = ep_el(config['episode_name_selector'])
                    if not name_el:
                        continue
                    name = name_el.text().strip()
                    if not name:
                        continue
                    
                    # Extract URL
                    url_el = ep_el(config['episode_url_selector'])
                    if not url_el:
                        continue
                    
                    partial_url = url_el.attr('href') or url_el.text().strip()
                    if not partial_url:
                        continue
                    
                    full_url = urljoin(base_url, partial_url)
                    
                    # Parse episode sort
                    episode_number = parse_episode_number(name)
                    episode_sort = EpisodeSort(episode_number) if episode_number else None
                    
                    episodes.append(WebSearchEpisodeInfo(
                        channel=channel_name,
                        name=name,
                        episode_sort_or_ep=episode_sort,
                        play_url=full_url
                    ))
            
            return episodes
            
        except Exception as e:
            print(f"Error in SelectorChannelFormatIndexGrouped.select: {e}")
            return []


# Format registry
_SUBJECT_FORMATS = {
    SelectorFormatId.SUBJECT_FORMAT_A: SelectorSubjectFormatA(),
    SelectorFormatId.SUBJECT_FORMAT_INDEXED: SelectorSubjectFormatIndexed(),
}

_CHANNEL_FORMATS = {
    SelectorFormatId.CHANNEL_FORMAT_NO_CHANNEL: SelectorChannelFormatNoChannel(),
    SelectorFormatId.CHANNEL_FORMAT_INDEX_GROUPED: SelectorChannelFormatIndexGrouped(),
}


def get_subject_format(format_id: str) -> Optional[SelectorSubjectFormat]:
    """Get subject format by ID"""
    return _SUBJECT_FORMATS.get(format_id)


def get_channel_format(format_id: str) -> Optional[SelectorChannelFormat]:
    """Get channel format by ID"""
    return _CHANNEL_FORMATS.get(format_id)


def list_subject_formats() -> List[str]:
    """List all available subject format IDs"""
    return list(_SUBJECT_FORMATS.keys())


def list_channel_formats() -> List[str]:
    """List all available channel format IDs"""  
    return list(_CHANNEL_FORMATS.keys())