"""
Media filtering utilities for web scraper
"""

from abc import ABC, abstractmethod
from typing import List, Set, Optional, Any
from ..models import Media, EpisodeSort


class MediaListFilterContext:
    """Context for media filtering operations"""
    
    def __init__(self, subject_names: Set[str], episode_sort: Optional[EpisodeSort] = None,
                 episode_ep: Optional[EpisodeSort] = None, episode_name: Optional[str] = None):
        self.subject_names = subject_names
        self.episode_sort = episode_sort
        self.episode_ep = episode_ep
        self.episode_name = episode_name


class MediaFilterCandidate:
    """Candidate for media filtering"""
    
    def __init__(self, original_title: str, episode_range: Optional[Any] = None):
        self.original_title = original_title
        self.episode_range = episode_range


class MediaListFilter(ABC):
    """Base class for media list filters"""
    
    @abstractmethod
    def apply_on(self, candidate: MediaFilterCandidate, context: MediaListFilterContext) -> bool:
        """Apply filter on candidate with given context"""
        pass


class ContainsSubjectNameFilter(MediaListFilter):
    """Filter that checks if media title contains any of the subject names"""
    
    def apply_on(self, candidate: MediaFilterCandidate, context: MediaListFilterContext) -> bool:
        title_lower = candidate.original_title.lower()
        
        for subject_name in context.subject_names:
            # Check for partial matches
            subject_words = subject_name.lower().split()
            if all(word in title_lower for word in subject_words if word):
                return True
        
        return False


class ContainsEpisodeInfoFilter(MediaListFilter):
    """Filter that checks if media contains episode information matching the query"""
    
    def apply_on(self, candidate: MediaFilterCandidate, context: MediaListFilterContext) -> bool:
        if not context.episode_sort and not context.episode_ep and not context.episode_name:
            return True  # No episode criteria to check
        
        title_lower = candidate.original_title.lower()
        
        # Check episode name if provided
        if context.episode_name:
            episode_name_lower = context.episode_name.lower()
            if episode_name_lower in title_lower:
                return True
        
        # Check episode number if provided
        if context.episode_sort:
            episode_num_str = str(context.episode_sort.value)
            # Look for episode number in various formats
            episode_patterns = [
                f"第{episode_num_str}集",
                f"第{episode_num_str}话", 
                f"ep{episode_num_str}",
                f"episode {episode_num_str}",
                f" {episode_num_str} ",  # Standalone number
            ]
            
            if any(pattern in title_lower for pattern in episode_patterns):
                return True
        
        return False


class QualityFilter(MediaListFilter):
    """Filter media by quality preferences"""
    
    def __init__(self, preferred_qualities: List[str]):
        self.preferred_qualities = [q.lower() for q in preferred_qualities]
    
    def apply_on(self, candidate: MediaFilterCandidate, context: MediaListFilterContext) -> bool:
        if not self.preferred_qualities:
            return True  # No quality filter
        
        title_lower = candidate.original_title.lower()
        
        # Check if any preferred quality is in the title
        return any(quality in title_lower for quality in self.preferred_qualities)


class LanguageFilter(MediaListFilter):
    """Filter media by subtitle language"""
    
    def __init__(self, preferred_languages: List[str]):
        self.preferred_languages = preferred_languages
        self.language_keywords = {
            'CHS': ['简', '简中', '简体'],
            'CHT': ['繁', '繁中', '繁体'],
            'JPN': ['日语', '日文'],
            'ENG': ['英语', '英文', 'eng'],
        }
    
    def apply_on(self, candidate: MediaFilterCandidate, context: MediaListFilterContext) -> bool:
        if not self.preferred_languages:
            return True  # No language filter
        
        title_lower = candidate.original_title.lower()
        
        for lang in self.preferred_languages:
            keywords = self.language_keywords.get(lang.upper(), [lang.lower()])
            if any(keyword in title_lower for keyword in keywords):
                return True
        
        return False


class MediaFilters:
    """Collection of common media filters"""
    
    CONTAINS_SUBJECT_NAME = ContainsSubjectNameFilter()
    CONTAINS_ANY_EPISODE_INFO = ContainsEpisodeInfoFilter()
    
    @staticmethod
    def create_quality_filter(qualities: List[str]) -> QualityFilter:
        return QualityFilter(qualities)
    
    @staticmethod
    def create_language_filter(languages: List[str]) -> LanguageFilter:
        return LanguageFilter(languages)


def apply_filters(candidates: List[Any], filters: List[MediaListFilter], 
                 context: MediaListFilterContext) -> List[Any]:
    """
    Apply a list of filters to candidates.
    
    Args:
        candidates: List of candidates to filter
        filters: List of filters to apply
        context: Filter context
        
    Returns:
        Filtered list of candidates
    """
    filtered = []
    
    for candidate in candidates:
        # Convert to MediaFilterCandidate if needed
        if not isinstance(candidate, MediaFilterCandidate):
            filter_candidate = MediaFilterCandidate(
                original_title=getattr(candidate, 'original_title', str(candidate)),
                episode_range=getattr(candidate, 'episode_range', None)
            )
        else:
            filter_candidate = candidate
        
        # Apply all filters
        if all(filter_obj.apply_on(filter_candidate, context) for filter_obj in filters):
            filtered.append(candidate)
    
    return filtered


def create_filters_for_subject(config) -> List[MediaListFilter]:
    """Create filters for subject-level filtering"""
    filters = []
    
    # Add subject name filter if enabled
    if getattr(config, 'filter_by_subject_name', False):
        filters.append(MediaFilters.CONTAINS_SUBJECT_NAME)
    
    return filters


def create_filters_for_episode(config) -> List[MediaListFilter]:
    """Create filters for episode-level filtering"""
    filters = []
    
    # Add episode info filter if enabled
    if getattr(config, 'filter_by_episode_sort', False):
        filters.append(MediaFilters.CONTAINS_ANY_EPISODE_INFO)
    
    return filters