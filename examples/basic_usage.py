#!/usr/bin/env python3
"""
Basic usage example for the Python web scraper.

This example demonstrates how to:
1. Create and configure a SelectorMediaSource
2. Perform searches for anime
3. Extract video URLs using the three-step pattern
"""

import asyncio
import sys
import os

# Add the web_scraper package to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_scraper.core import SelectorMediaSource, ThreeStepWebMediaSource
from web_scraper.models import (
    SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
    SelectorSubjectFormatConfig, SelectorChannelFormatConfig, MatchVideoConfig
)


def create_example_config() -> SelectorSearchConfig:
    """Create an example configuration for a hypothetical anime site"""
    return SelectorSearchConfig(
        # Search configuration
        search_url="https://example-anime-site.com/search?keyword={keyword}",
        search_use_only_first_word=True,
        search_remove_special=True,
        
        # Subject format configuration  
        subject_format_id="subject_format_a",
        subject_format_config=SelectorSubjectFormatConfig(
            subject_selector=".search-result-item",
            name_selector=".anime-title",
            url_selector="a.anime-link"
        ),
        
        # Episode format configuration
        channel_format_id="channel_format_no_channel", 
        channel_format_config=SelectorChannelFormatConfig(
            episode_selector=".episode-item",
            name_selector=".episode-title",
            url_selector="a.episode-link"
        ),
        
        # Other settings
        default_resolution="1080P",
        default_subtitle_language="CHS",
        request_interval_seconds=2.0,
    )


async def test_selector_media_source():
    """Test the SelectorMediaSource with example configuration"""
    print("=== Testing SelectorMediaSource ===")
    
    config = create_example_config()
    source = SelectorMediaSource("example-source", config)
    
    # Check connection (will fail since it's an example URL)
    print(f"Connection status: {source.check_connection()}")
    
    # Create a fetch request
    request = MediaFetchRequest(
        subject_names=["进击的巨人", "Attack on Titan"],
        episode_sort=EpisodeSort(1),
        episode_name="第1集"
    )
    
    print(f"Created fetch request for: {request.subject_names}")
    print(f"Source info: {source.info}")
    
    # Note: This would fail with the example URL, but shows the API
    try:
        matches = list(source.fetch(request))
        print(f"Found {len(matches)} matches")
        
        for i, match in enumerate(matches[:3]):  # Show first 3
            print(f"  Match {i+1}: {match.media.original_title}")
            print(f"    URL: {match.media.download.url}")
            print(f"    Episode: {match.media.episode_range}")
            
    except Exception as e:
        print(f"Expected error (example URL): {e}")


class ExampleThreeStepSource(ThreeStepWebMediaSource):
    """Example implementation of ThreeStepWebMediaSource"""
    
    def parse_bangumi_search(self, document):
        """Parse search results - example implementation"""
        from web_scraper.models import Bangumi
        
        # Example: extract anime from search results
        bangumi_list = []
        items = document.select(".anime-item")
        
        for i, item in enumerate(items[:5]):  # Limit to 5 for demo
            title_elem = item.select_one(".anime-title")
            link_elem = item.select_one("a")
            
            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href', '')
                
                if not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                
                bangumi_list.append(Bangumi(
                    internal_id=f"demo_{i}",
                    name=title,
                    url=url
                ))
        
        return bangumi_list
    
    async def search(self, name, query_request):
        """Search implementation - returns demo data"""
        from web_scraper.models import Bangumi
        
        print(f"Searching for: {name}")
        
        # Return demo bangumi for testing
        return [
            Bangumi(
                internal_id="demo_1",
                name=f"Demo Anime: {name}",
                url=f"{self.base_url}/anime/demo-anime-1"
            ),
            Bangumi(
                internal_id="demo_2", 
                name=f"Demo Anime 2: {name}",
                url=f"{self.base_url}/anime/demo-anime-2"
            )
        ]
    
    def parse_episode_list(self, document):
        """Parse episode list - example implementation"""
        from web_scraper.models import Episode
        
        episodes = []
        episode_items = document.select(".episode-item")
        
        for i, item in enumerate(episode_items[:3]):  # Limit for demo
            name_elem = item.select_one(".episode-name")
            link_elem = item.select_one("a")
            
            if name_elem and link_elem:
                name = name_elem.get_text(strip=True)
                url = link_elem.get('href', '')
                
                if not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                
                episodes.append(Episode(
                    name=name or f"第{i+1}集",
                    url=url,
                    channel="HD"
                ))
        
        return episodes


async def test_three_step_source():
    """Test the ThreeStepWebMediaSource with example implementation"""
    print("\n=== Testing ThreeStepWebMediaSource ===")
    
    source = ExampleThreeStepSource(
        media_source_id="demo-three-step",
        base_url="https://demo-anime-site.com"
    )
    
    # Create a fetch request
    request = MediaFetchRequest(
        subject_names=["进击的巨人"],
        episode_sort=EpisodeSort(1)
    )
    
    print(f"Three-step source info:")
    print(f"  Media Source ID: {source.media_source_id}")
    print(f"  Base URL: {source.base_url}")
    print(f"  Connection: {source.check_connection()}")
    
    # Test search functionality
    bangumi_list = await source.search("进击的巨人", request)
    print(f"\nFound {len(bangumi_list)} anime:")
    for bangumi in bangumi_list:
        print(f"  - {bangumi.name} ({bangumi.internal_id})")
    
    # Note: Full fetch would require actual HTML content
    print("\nThree-step pattern demonstrated successfully!")


def demonstrate_configuration():
    """Demonstrate various configuration options"""
    print("\n=== Configuration Examples ===")
    
    # Basic configuration
    basic_config = SelectorSearchConfig(
        search_url="https://site.com/search?q={keyword}",
        subject_format_config=SelectorSubjectFormatConfig(
            subject_selector=".result",
            name_selector=".title", 
            url_selector="a"
        )
    )
    
    print("Basic configuration created:")
    print(f"  Search URL: {basic_config.search_url}")
    print(f"  Base URL: {basic_config.final_base_url}")
    print(f"  Request interval: {basic_config.request_interval_seconds}s")
    
    # Advanced configuration
    advanced_config = SelectorSearchConfig(
        search_url="https://advanced-site.com/api/search/{keyword}",
        search_use_subject_names_count=3,
        request_interval_seconds=5.0,
        only_supports_players=["vlc", "exoplayer"],
        
        subject_format_config=SelectorSubjectFormatConfig(
            subject_selector=".anime-card",
            name_selector="h3.title",
            url_selector="a.details-link"
        ),
        
        channel_format_config=SelectorChannelFormatConfig(
            episode_selector=".ep-list .ep-item",
            name_selector=".ep-title",
            url_selector=".ep-link",
            channel_selector=".quality-tag"
        ),
        
        # Video matching
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            match_video_url=r"(\.mp4|\.m3u8|streaming\.com)",
            cookies="quality=1080;lang=zh"
        )
    )
    
    print("\nAdvanced configuration features:")
    print(f"  Multiple subject names: {advanced_config.search_use_subject_names_count}")
    print(f"  Player restrictions: {advanced_config.only_supports_players}")
    print(f"  Video URL regex: {advanced_config.match_video.match_video_url}")


async def main():
    """Main demo function"""
    print("* Animeko Python Web Scraper Demo")
    print("=" * 50)
    
    # Test basic functionality
    await test_selector_media_source()
    await test_three_step_source()
    
    # Show configuration options
    demonstrate_configuration()
    
    print("\n[OK] Demo completed successfully!")
    print("\nNext steps:")
    print("1. Customize the CSS selectors for your target site")
    print("2. Configure video URL matching patterns")
    print("3. Add error handling and logging")
    print("4. Implement rate limiting and caching")


if __name__ == "__main__":
    asyncio.run(main())