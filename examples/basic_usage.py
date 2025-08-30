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
from web_scraper.utils.logger import logger

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
    logger.info("正在测试 SelectorMediaSource")
    
    config = create_example_config()
    source = SelectorMediaSource("example-source", config)
    
    # Check connection (will fail since it's an example URL)
    logger.info(f"连接状态: {source.check_connection()}")
    
    # Create a fetch request
    request = MediaFetchRequest(
        subject_names=["进击的巨人", "Attack on Titan"],
        episode_sort=EpisodeSort(1),
        episode_name="第1集"
    )
    
    logger.info(f"为以下主题创建了查询请求: {request.subject_names}")
    logger.info(f"源信息: {source.info}")
    
    # Note: This would fail with the example URL, but shows the API
    try:
        matches = list(source.fetch(request))
        logger.success(f"找到 {len(matches)} 个匹配结果")
        
        for i, match in enumerate(matches[:3]):  # Show first 3
            logger.info(f"  匹配 {i+1}: {match.media.original_title}")
            logger.info(f"    URL: {match.media.download.url}")
            logger.info(f"    剧集: {match.media.episode_range}")
            
    except Exception as e:
        logger.warning(f"预期错误（示例 URL）: {e}")


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
        
        logger.info(f"正在搜索: {name}")
        
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
    logger.info("正在测试 ThreeStepWebMediaSource")
    
    source = ExampleThreeStepSource(
        media_source_id="demo-three-step",
        base_url="https://demo-anime-site.com"
    )
    
    # Create a fetch request
    request = MediaFetchRequest(
        subject_names=["进击的巨人"],
        episode_sort=EpisodeSort(1)
    )
    
    logger.info(f"三步源信息:")
    logger.info(f"  媒体源 ID: {source.media_source_id}")
    logger.info(f"  基本 URL: {source.base_url}")
    logger.info(f"  连接: {source.check_connection()}")
    
    # Test search functionality
    bangumi_list = await source.search("进击的巨人", request)
    logger.success(f"找到 {len(bangumi_list)} 个动漯:")
    for bangumi in bangumi_list:
        logger.info(f"  - {bangumi.name} ({bangumi.internal_id})")
    
    # Note: Full fetch would require actual HTML content
    logger.success("三步模式演示成功！")


def demonstrate_configuration():
    """Demonstrate various configuration options"""
    logger.info("配置示例")
    
    # Basic configuration
    basic_config = SelectorSearchConfig(
        search_url="https://site.com/search?q={keyword}",
        subject_format_config=SelectorSubjectFormatConfig(
            subject_selector=".result",
            name_selector=".title", 
            url_selector="a"
        )
    )
    
    logger.info("基本配置已创建:")
    logger.info(f"  搜索 URL: {basic_config.search_url}")
    logger.info(f"  基本 URL: {basic_config.final_base_url}")
    logger.info(f"  请求间隔: {basic_config.request_interval_seconds}秒")
    
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
    
    logger.info("高级配置功能:")
    logger.info(f"  多个主题名称: {advanced_config.search_use_subject_names_count}")
    logger.info(f"  播放器限制: {advanced_config.only_supports_players}")
    logger.info(f"  视频 URL 正则: {advanced_config.match_video.match_video_url}")


async def main():
    """Main demo function"""
    logger.info("* Animeko Python 网页爬虫演示")
    logger.info("=" * 50)
    
    # Test basic functionality
    await test_selector_media_source()
    await test_three_step_source()
    
    # Show configuration options
    demonstrate_configuration()
    
    logger.success("演示成功完成！")
    logger.info("下一步:")
    logger.info("1. 为目标网站自定义 CSS 选择器")
    logger.info("2. 配置视频 URL 匹配模式")
    logger.info("3. 添加错误处理和日志")
    logger.info("4. 实现限速和缓存")


if __name__ == "__main__":
    asyncio.run(main())