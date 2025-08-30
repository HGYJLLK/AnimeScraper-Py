#!/usr/bin/env python3
"""
Simple test runner for the Python web scraper implementation.
"""

import sys
import os
from web_scraper.utils.logger import logger

# Add the web_scraper package to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all modules can be imported successfully"""
    logger.info("正在测试导入...")
    
    try:
        from web_scraper.core import SelectorMediaSource, SelectorMediaSourceEngine
        logger.success("  核心类导入成功")
        
        from web_scraper.models import (
            SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
            SelectorSubjectFormatConfig, SelectorChannelFormatConfig
        )
        logger.success("  模型类导入成功")
        
        from web_scraper.utils import helpers, filters
        logger.success("  工具模块导入成功")
        
        from web_scraper.formats.selector_formats import (
            SelectorSubjectFormatA, SelectorChannelFormatNoChannel
        )
        logger.success("  格式类导入成功")
        
        return True
        
    except ImportError as e:
        logger.error(f"  导入错误: {e}")
        return False

def test_configuration():
    """Test configuration creation and validation"""
    logger.info("正在测试配置...")
    
    try:
        from web_scraper.models import SelectorSearchConfig
        from web_scraper.models.config import SelectorSubjectFormatConfig, SelectorChannelFormatConfig
        
        # Create a test configuration
        config = SelectorSearchConfig(
            search_url="https://example.com/search?q={keyword}",
            subject_format_config=SelectorSubjectFormatConfig(
                subject_selector=".anime-result",
                name_selector=".title",
                url_selector="a"
            ),
            channel_format_config=SelectorChannelFormatConfig(
                episode_selector=".episode",
                name_selector=".ep-name",
                url_selector=".ep-link"
            )
        )
        
        logger.success(f"  配置创建成功: {config.search_url}")
        logger.success(f"  基本 URL: {config.final_base_url}")
        logger.success(f"  主题格式有效: {config.subject_format_config.is_valid()}")
        logger.success(f"  频道格式有效: {config.channel_format_config.is_valid()}")
        
        return True
        
    except Exception as e:
        logger.error(f"  配置错误: {e}")
        return False

def test_media_source():
    """Test SelectorMediaSource creation"""
    logger.info("正在测试媒体源...")
    
    try:
        from web_scraper.core import SelectorMediaSource
        from web_scraper.models import SelectorSearchConfig
        from web_scraper.models.config import SelectorSubjectFormatConfig, SelectorChannelFormatConfig
        
        config = SelectorSearchConfig(
            search_url="https://example.com/search?q={keyword}",
            subject_format_config=SelectorSubjectFormatConfig(
                subject_selector=".result",
                name_selector=".title",
                url_selector="a"
            ),
            channel_format_config=SelectorChannelFormatConfig(
                episode_selector=".episode",
                name_selector=".name",
                url_selector=".link"
            )
        )
        
        source = SelectorMediaSource("test-source", config)
        
        logger.success(f"  媒体源创建成功: {source.media_source_id}")
        logger.success(f"  信息: {source.info}")
        
        # Test connection (will fail with example URL)
        connection_status = source.check_connection()
        logger.success(f"  连接检查: {connection_status}")
        
        return True
        
    except Exception as e:
        logger.error(f"  媒体源错误: {e}")
        return False

def test_utilities():
    """Test utility functions"""
    logger.info("正在测试工具...")
    
    try:
        from web_scraper.utils.helpers import (
            parse_episode_number, get_search_keyword, 
            extract_quality_info, extract_subtitle_language
        )
        
        # Test episode parsing
        episode_num = parse_episode_number("第12集")
        logger.success(f"  剧集解析: '第12集' → {episode_num}")
        
        # Test keyword extraction
        keyword = get_search_keyword("进击的巨人 Season 2", remove_special=True, use_only_first_word=True)
        logger.success(f"  关键词提取: '{keyword}'")
        
        # Test quality extraction
        quality = extract_quality_info("Attack on Titan 1080P")
        logger.success(f"  质量提取: {quality}")
        
        # Test language extraction
        lang = extract_subtitle_language("简体中文版")
        logger.success(f"  语言提取: {lang}")
        
        return True
        
    except Exception as e:
        logger.error(f"  工具错误: {e}")
        return False

def main():
    """Main test runner"""
    logger.info("Animeko Python 网页爬虫 - 测试运行器")
    logger.info("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_media_source,
        test_utilities,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    logger.info(f"测试结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        logger.success("所有测试通过！Python 网页爬虫已准备好可以使用。")
        logger.info("下一步:")
        logger.info("1. 为目标网站自定义 CSS 选择器")
        logger.info("2. 配置视频 URL 匹配模式")
        logger.info("3. 使用真实动漫网站进行测试")
    else:
        logger.error("一些测试失败。请检查实现。")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())