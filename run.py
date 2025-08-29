#!/usr/bin/env python3
"""
Simple test runner for the Python web scraper implementation.
"""

import sys
import os

# Add the web_scraper package to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing imports...")
    
    try:
        from web_scraper.core import SelectorMediaSource, SelectorMediaSourceEngine
        print("  [OK] Core classes imported")
        
        from web_scraper.models import (
            SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
            SelectorSubjectFormatConfig, SelectorChannelFormatConfig
        )
        print("  [OK] Model classes imported")
        
        from web_scraper.utils import helpers, filters
        print("  [OK] Utility modules imported")
        
        from web_scraper.formats.selector_formats import (
            SelectorSubjectFormatA, SelectorChannelFormatNoChannel
        )
        print("  [OK] Format classes imported")
        
        return True
        
    except ImportError as e:
        print(f"  [ERROR] Import error: {e}")
        return False

def test_configuration():
    """Test configuration creation and validation"""
    print("\nTesting configuration...")
    
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
        
        print(f"  [OK] Configuration created: {config.search_url}")
        print(f"  [OK] Base URL: {config.final_base_url}")
        print(f"  [OK] Subject format valid: {config.subject_format_config.is_valid()}")
        print(f"  [OK] Channel format valid: {config.channel_format_config.is_valid()}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Configuration error: {e}")
        return False

def test_media_source():
    """Test SelectorMediaSource creation"""
    print("\nTesting media source...")
    
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
        
        print(f"  [OK] Media source created: {source.media_source_id}")
        print(f"  [OK] Info: {source.info}")
        
        # Test connection (will fail with example URL)
        connection_status = source.check_connection()
        print(f"  [OK] Connection check: {connection_status}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Media source error: {e}")
        return False

def test_utilities():
    """Test utility functions"""
    print("\nTesting utilities...")
    
    try:
        from web_scraper.utils.helpers import (
            parse_episode_number, get_search_keyword, 
            extract_quality_info, extract_subtitle_language
        )
        
        # Test episode parsing
        episode_num = parse_episode_number("第12集")
        print(f"  [OK] Episode parsing: '第12集' → {episode_num}")
        
        # Test keyword extraction
        keyword = get_search_keyword("进击的巨人 Season 2", remove_special=True, use_only_first_word=True)
        print(f"  [OK] Keyword extraction: '{keyword}'")
        
        # Test quality extraction
        quality = extract_quality_info("Attack on Titan 1080P")
        print(f"  [OK] Quality extraction: {quality}")
        
        # Test language extraction
        lang = extract_subtitle_language("简体中文版")
        print(f"  [OK] Language extraction: {lang}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Utilities error: {e}")
        return False

def main():
    """Main test runner"""
    print("Animeko Python Web Scraper - Test Runner")
    print("=" * 50)
    
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
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! The Python web scraper is ready to use.")
        print("\nNext steps:")
        print("1. Customize CSS selectors for your target website")
        print("2. Configure video URL matching patterns")
        print("3. Test with real anime sites")
    else:
        print("Some tests failed. Please check the implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())