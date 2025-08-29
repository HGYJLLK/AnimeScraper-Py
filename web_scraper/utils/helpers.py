"""
Utility helper functions for web scraper
"""

import re
from typing import Optional
from urllib.parse import quote_plus


def encode_url_segment(text: str) -> str:
    """URL encode a text segment"""
    return quote_plus(text)


def get_search_keyword(subject_name: str, remove_special: bool = True, 
                      use_only_first_word: bool = True) -> str:
    """
    Extract search keyword from subject name.
    
    Args:
        subject_name: The original subject name
        remove_special: Whether to remove special characters
        use_only_first_word: Whether to use only the first word
    
    Returns:
        Processed keyword for searching
    """
    keyword = subject_name
    
    if remove_special:
        # Remove special characters, keep only word characters and spaces
        keyword = re.sub(r'[^\w\s]', ' ', keyword)
        keyword = re.sub(r'\s+', ' ', keyword)  # Normalize whitespace
    
    if use_only_first_word:
        words = keyword.split()
        keyword = words[0] if words else keyword
    
    return keyword.strip()


def parse_episode_number(episode_name: str) -> Optional[int]:
    """
    Parse episode number from episode name.
    
    Supports patterns like:
    - 第1集, 第01集
    - 第1话, 第01话  
    - EP01, EP1
    - 01集, 1集
    - 01话, 1话
    - Just numbers: 01, 1
    
    Args:
        episode_name: The episode name to parse
        
    Returns:
        Episode number as integer, or None if not found
    """
    patterns = [
        r'第(\d+)集',      # 第1集
        r'第(\d+)话',      # 第1话
        r'EP(\d+)',        # EP01
        r'(\d+)集',        # 01集
        r'(\d+)话',        # 01话
        r'^(\d+)$',        # Just number
        r'Episode\s*(\d+)', # Episode 1
        r'Ep\s*(\d+)',     # Ep 1
    ]
    
    for pattern in patterns:
        match = re.search(pattern, episode_name, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def is_video_url(url: str) -> bool:
    """
    Check if URL points to a video file.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL appears to be a video file
    """
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm']
    url_lower = url.lower()
    
    # Check file extension
    if any(url_lower.endswith(ext) for ext in video_extensions):
        return True
    
    # Check for streaming formats
    streaming_indicators = ['m3u8', 'playlist', 'stream', 'video']
    if any(indicator in url_lower for indicator in streaming_indicators):
        return True
    
    return False


def normalize_title(title: str) -> str:
    """
    Normalize anime title for better matching.
    
    Args:
        title: Original title
        
    Returns:
        Normalized title
    """
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title.strip())
    
    # Remove common suffixes/prefixes
    suffixes_to_remove = [
        r'\s*\(.*?\)',      # Remove parentheses content
        r'\s*\[.*?\]',      # Remove bracket content  
        r'\s*Season\s*\d+', # Remove season info
        r'\s*S\d+',         # Remove S1, S2 etc
    ]
    
    for suffix in suffixes_to_remove:
        title = re.sub(suffix, '', title, flags=re.IGNORECASE)
    
    return title.strip()


def extract_quality_info(title: str) -> Optional[str]:
    """
    Extract video quality information from title.
    
    Args:
        title: Title to extract quality from
        
    Returns:
        Quality string like "1080P", "720P" etc, or None if not found
    """
    quality_patterns = [
        r'(\d{3,4}[pP])',      # 720p, 1080P etc
        r'([24]K)',             # 2K, 4K
        r'(HD)',               # HD
        r'(UHD)',              # UHD
    ]
    
    for pattern in quality_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None


def extract_subtitle_language(text: str) -> Optional[str]:
    """
    Extract subtitle language from text.
    
    Args:
        text: Text to extract language from
        
    Returns:
        Language code like "CHS", "CHT", "JPN" etc, or None if not found
    """
    language_mappings = {
        '简': 'CHS',
        '简中': 'CHS', 
        '简体': 'CHS',
        '繁': 'CHT',
        '繁中': 'CHT',
        '繁体': 'CHT',
        '中文': 'CHT',  # Default to traditional
        '日语': 'JPN',
        '日文': 'JPN',
        '英语': 'ENG',
        '英文': 'ENG',
    }
    
    for key, lang_code in language_mappings.items():
        if key in text:
            return lang_code
    
    return None