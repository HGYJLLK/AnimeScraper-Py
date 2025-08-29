# AnimeScraper-Py

A Python port of the Kotlin web scraper from the Animeko project, maintaining identical functionality for CSS-based web parsing, three-step scraping flow, and configurable selector rules.

## Features

- **CSS Selector-based Parsing**: Flexible CSS selector configuration for different website structures
- **Three-step Scraping Flow**: 
  1. Search anime → Find anime list
  2. Get episodes lists → Extract episode list for each anime
  3. Extract video URLs → Get actual playable URLs
- **Configurable Rules**: Customizable selector rules and parsing logic
- **Rate Limiting**: Built-in request throttling and retry logic
- **Video URL Extraction**: Advanced video URL matching with regex patterns
- **Multiple Formats**: Support for different website layouts and structures

## Architecture

### Core Components

- **`SelectorMediaSource`**: Main media source class orchestrating CSS selector-based scraping
- **`SelectorMediaSourceEngine`**: Core parsing engine handling the three-phase flow
- **`ThreeStepWebMediaSource`**: Abstract base for the three-step scraping pattern
- **Configuration System**: Flexible configuration for different site structures

### Directory Structure

```
python/web_scraper/
├── __init__.py
├── core/
│   ├── engine.py          # SelectorMediaSourceEngine
│   ├── source.py          # SelectorMediaSource  
│   └── three_step_source.py  # ThreeStepWebMediaSource
├── models/
│   ├── media.py           # Media data classes
│   ├── search.py          # Search result classes
│   └── config.py          # Configuration classes
├── formats/
│   └── selector_formats.py   # Format handlers for different site structures
└── utils/
    ├── helpers.py         # Utility functions
    └── filters.py         # Media filtering utilities
```

## Quick Start

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Import the scraper:
```python
from web_scraper.core import SelectorMediaSource, ThreeStepWebMediaSource
from web_scraper.models import SelectorSearchConfig, MediaFetchRequest
```

### Basic Usage

```python
import asyncio
from web_scraper.core import SelectorMediaSource
from web_scraper.models import (
    SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
    SelectorSubjectFormatConfig, SelectorChannelFormatConfig
)

# Configure the scraper
config = SelectorSearchConfig(
    search_url="https://example-site.com/search?keyword={keyword}",
    
    # Subject parsing configuration
    subject_format_config=SelectorSubjectFormatConfig(
        subject_selector=".search-result-item",
        name_selector=".anime-title",
        url_selector="a.anime-link"
    ),
    
    # Episode parsing configuration  
    channel_format_config=SelectorChannelFormatConfig(
        episode_selector=".episode-item",
        name_selector=".episode-title",
        url_selector="a.episode-link"
    ),
)

# Create media source
source = SelectorMediaSource("my-source", config)

# Create search request
request = MediaFetchRequest(
    subject_names=["进击的巨人", "Attack on Titan"],
    episode_sort=EpisodeSort(1)
)

# Perform search
matches = list(source.fetch(request))
for match in matches:
    print(f"Found: {match.media.original_title}")
    print(f"Video URL: {match.media.download.url}")
```

### Three-Step Pattern

```python
from web_scraper.core import ThreeStepWebMediaSource
from web_scraper.models import Bangumi, Episode

class MyAnimeScraper(ThreeStepWebMediaSource):
    def parse_bangumi_search(self, document):
        # Step 1: Parse search results for anime list
        bangumi_list = []
        for item in document.select(".anime-result"):
            title = item.select_one(".title").get_text()
            url = item.select_one("a")["href"]
            bangumi_list.append(Bangumi(
                internal_id=hash(title) % 10000,
                name=title,
                url=url
            ))
        return bangumi_list
    
    async def search(self, name, query):
        # Implement search logic
        response = self.session.get(f"{self.base_url}/search?q={name}")
        document = BeautifulSoup(response.text, 'html.parser')
        return self.parse_bangumi_search(document)
    
    def parse_episode_list(self, document):
        # Step 2: Parse episode list from anime page
        episodes = []
        for ep in document.select(".episode"):
            name = ep.select_one(".ep-title").get_text()
            url = ep.select_one("a")["href"] 
            episodes.append(Episode(name=name, url=url))
        return episodes

# Usage
scraper = MyAnimeScraper("my-scraper", "https://anime-site.com")
request = MediaFetchRequest(subject_names=["进击的巨人"])
matches = list(await scraper.fetch(request))
```

## Configuration Options

### Search Configuration

```python
config = SelectorSearchConfig(
    # Basic search settings
    search_url="https://site.com/search?keyword={keyword}",
    search_use_only_first_word=True,        # Use only first word of anime name
    search_remove_special=True,             # Remove special characters
    search_use_subject_names_count=2,       # Try multiple subject names
    request_interval_seconds=3.0,           # Rate limiting
    
    # Subject format (search results page)
    subject_format_id="subject_format_a",
    subject_format_config=SelectorSubjectFormatConfig(
        subject_selector=".search-result",   # Container for each result
        name_selector=".title",              # Anime name within container
        url_selector="a"                     # Link to anime page
    ),
    
    # Channel format (episode list page)
    channel_format_id="channel_format_no_channel", 
    channel_format_config=SelectorChannelFormatConfig(
        episode_selector=".episode",        # Container for each episode
        name_selector=".ep-name",           # Episode name
        url_selector=".ep-link",            # Episode video link
        channel_selector=".quality"        # Optional: video quality/channel
    ),
    
    # Media settings
    default_resolution="1080P",
    default_subtitle_language="CHS",
    only_supports_players=["vlc", "exoplayer"],
    
    # Video URL matching
    match_video=MatchVideoConfig(
        enable_nested_url=True,
        match_video_url=r"(\.mp4|\.m3u8|streaming\.com)",
        cookies="quality=1080;lang=zh"
    )
)
```

### Format Types

The scraper supports different website structures through format handlers:

#### Subject Formats
- **`subject_format_a`**: Standard CSS selector-based extraction
- **`subject_format_indexed`**: For indexed/numbered listings

#### Channel Formats  
- **`channel_format_no_channel`**: Direct episode listing without channels
- **`channel_format_index_grouped`**: Episodes grouped by channel/quality

## Advanced Features

### Custom Filtering

```python
from web_scraper.utils.filters import MediaFilters, MediaListFilterContext

# Apply custom filters
context = MediaListFilterContext(
    subject_names={"进击的巨人"},
    episode_sort=EpisodeSort(1)
)

filters = [
    MediaFilters.CONTAINS_SUBJECT_NAME,
    MediaFilters.CONTAINS_ANY_EPISODE_INFO,
    MediaFilters.create_quality_filter(["1080P", "720P"]),
    MediaFilters.create_language_filter(["CHS", "CHT"])
]

filtered_media = apply_filters(media_list, filters, context)
```

### Video URL Matching

```python
# Configure video URL extraction
match_config = MatchVideoConfig(
    enable_nested_url=True,
    match_nested_url=r"(m3u8|vip|streaming\.php)",
    match_video_url=r"(\.mp4|\.mkv|\.m3u8)",
    add_headers_to_video=VideoHeaders(
        user_agent="Custom User Agent",
        referer="https://site.com"
    )
)

# Use in source
result = source.match_web_video("https://site.com/video.m3u8")
if result["action"] == "matched":
    video_url = result["video_url"]
    headers = result["headers"]
```

## Error Handling

The scraper includes built-in error handling and retry logic:

```python
# Automatic retries for failed requests
matches = list(source.fetch(request))  # Handles retries internally

# Connection checking
status = source.check_connection()
if status == "SUCCESS":
    # Proceed with scraping
    pass
```

## Examples

See the `examples/` directory for complete working examples:

- **`basic_usage.py`**: Basic scraper setup and usage
- **`custom_scraper.py`**: Custom three-step scraper implementation  
- **`advanced_config.py`**: Advanced configuration examples

## Compatibility

This Python implementation maintains full compatibility with the original Kotlin version:

- [OK] Same three-step scraping flow
- [OK] Identical CSS selector configuration
- [OK] Compatible video URL extraction logic
- [OK] Same filtering and matching behavior
- [OK] Equivalent rate limiting and retry logic

## Requirements

- Python 3.7+
- requests >= 2.28.0
- beautifulsoup4 >= 4.11.0  
- pyquery >= 1.4.3
- lxml >= 4.9.0
- urllib3 >= 1.26.0

## License

This project follows the same license as the original Animeko project (GNU AGPLv3).