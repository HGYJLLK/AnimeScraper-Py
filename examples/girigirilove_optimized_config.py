#!/usr/bin/env python3
"""
girigirilove 优化配置
基于HTML分析结果的精准配置
"""

import sys
import os
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web_scraper.core import SelectorMediaSource
from web_scraper.models import (
    SelectorSearchConfig, MediaFetchRequest, EpisodeSort,
    SelectorSubjectFormatConfig, SelectorChannelFormatConfig, MatchVideoConfig
)
from web_scraper.utils.logger import logger


def create_optimized_config():
    """
    基于HTML分析结果的优化配置
    
    发现的最佳选择器:
    - 容器: li
    - 标题: a  
    - 链接: a
    """
    return SelectorSearchConfig(
        # 使用发现的正确URL格式
        search_url="https://anime.girigirilove.com/search/-------------/?wd={keyword}",
        
        # 搜索设置
        search_use_only_first_word=False,
        search_remove_special=False,
        search_use_subject_names_count=2,
        
        # 请求设置
        request_interval_seconds=2.0,
        
        # 主题格式配置 - 基于HTML分析的精准选择器
        subject_format_config=SelectorSubjectFormatConfig(
            # 使用发现的有效选择器
            subject_selector="li",
            name_selector="a",
            url_selector="a"
        ),
        
        # 频道格式配置 - 剧集页面的选择器
        channel_format_config=SelectorChannelFormatConfig(
            # 基于常见模式，需要进一步分析剧集页面
            episode_selector=".public-list-box, .vod-title, li, .episode-item",
            name_selector="a, .title, .vod-title",
            url_selector="a"
        ),
        
        # 视频匹配配置
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            match_video_url=r"(\.mp4|\.m3u8|/play/|/video/|stream|watch|/GV\d+/)",
            cookies="",
        ),
        
        default_resolution="1080P",
        default_subtitle_language="CHS"
    )


def create_filtered_config():
    """
    创建过滤版本的配置
    过滤掉非动漫相关的链接
    """
    return SelectorSearchConfig(
        search_url="https://anime.girigirilove.com/search/-------------/?wd={keyword}",
        
        search_use_only_first_word=False,
        search_remove_special=False,
        search_use_subject_names_count=2,
        request_interval_seconds=2.0,
        
        # 更精确的选择器，尝试过滤出真正的搜索结果
        subject_format_config=SelectorSubjectFormatConfig(
            # 尝试更具体的容器选择器
            subject_selector=".public-list-box, .vod-title, li:has(a[href*='/GV'])",
            name_selector="a",
            url_selector="a[href*='/GV'], a[href*='/show/']"
        ),
        
        channel_format_config=SelectorChannelFormatConfig(
            episode_selector=".public-list-box, .vod-title, li",
            name_selector="a, .title",
            url_selector="a"
        ),
        
        match_video=MatchVideoConfig(
            enable_nested_url=True,
            match_video_url=r"(\.mp4|\.m3u8|/play/|/video/|stream|watch|/GV\d+/)",
            cookies="",
        ),
        
        default_resolution="1080P",
        default_subtitle_language="CHS"
    )


class OptimizedGirigiriloveSource(SelectorMediaSource):
    """
    优化的girigirilove数据源
    添加结果过滤和验证
    """
    
    def __init__(self, media_source_id: str, config: SelectorSearchConfig, session=None):
        super().__init__(media_source_id, config, session)
    
    def _is_valid_anime_link(self, url: str, title: str) -> bool:
        """
        验证是否是有效的动漫链接
        过滤掉导航链接、广告链接等
        """
        if not url or not title:
            return False
            
        # 过滤掉明显的非动漫链接
        invalid_patterns = [
            'label/',           # 标签页
            'syogames.com',     # 游戏网站
            'girigirilove.top', # 其他网站
            'javascript:',      # JS链接
            '#',               # 锚点链接
        ]
        
        for pattern in invalid_patterns:
            if pattern in url.lower():
                return False
        
        # 过滤掉明显的导航标题
        invalid_titles = [
            '点击广告',
            '游戏',
            '发布页',
            '联萌',
            '日番',
            '劇場版',
        ]
        
        for invalid_title in invalid_titles:
            if title.strip() == invalid_title:
                return False
        
        # 优先保留看起来像动漫的链接
        valid_patterns = [
            '/GV',      # GV开头的ID
            '/show/',   # show页面
        ]
        
        for pattern in valid_patterns:
            if pattern in url:
                return True
                
        return False
    
    async def search(self, search_config, query):
        """覆盖搜索方法添加结果过滤"""
        # URL编码
        encoded_keyword = quote(query.subject_name)
        original_url = search_config.search_url
        search_config.search_url = original_url.replace('{keyword}', encoded_keyword)
        
        logger.info(f"搜索URL: {search_config.search_url}")
        
        try:
            # 调用父类搜索
            results = await super().search(search_config, query)
            
            # 过滤结果
            filtered_results = []
            for media in results:
                url = media.download.url if media.download else ""
                title = media.original_title
                
                if self._is_valid_anime_link(url, title):
                    filtered_results.append(media)
                    logger.debug(f"保留结果: {title} -> {url}")
                else:
                    logger.debug(f"过滤掉: {title} -> {url}")
            
            logger.info(f"过滤后结果: {len(filtered_results)}/{len(results)}")
            return filtered_results
            
        finally:
            # 恢复原始URL
            search_config.search_url = original_url


def test_optimized_config():
    """测试优化配置"""
    logger.info("🎯 测试优化的girigirilove配置")
    logger.info("=" * 60)
    
    # 测试基本配置
    logger.info("\n=== 测试基本优化配置 ===")
    config = create_optimized_config()
    source = OptimizedGirigiriloveSource("girigirilove-optimized", config)
    
    test_search_functionality(source, "基本优化配置")
    
    # 测试过滤配置
    logger.info("\n=== 测试过滤配置 ===")
    filtered_config = create_filtered_config()
    filtered_source = OptimizedGirigiriloveSource("girigirilove-filtered", filtered_config)
    
    test_search_functionality(filtered_source, "过滤配置")


def test_search_functionality(source, config_name):
    """测试搜索功能"""
    logger.info(f"测试配置: {config_name}")
    
    # 测试多个关键词
    test_queries = [
        "进击的巨人",
        "鬼灭之刃", 
        "海贼王",
        "火影忍者"
    ]
    
    for query in test_queries:
        logger.info(f"\n--- 搜索: {query} ---")
        
        request = MediaFetchRequest(
            subject_names=[query],
            episode_sort=EpisodeSort(1)
        )
        
        try:
            matches = list(source.fetch(request))
            
            if matches:
                logger.success(f"✓ 找到 {len(matches)} 个结果:")
                for i, match in enumerate(matches[:5]):  # 显示前5个
                    title = match.media.original_title
                    url = match.media.download.url if match.media.download else ""
                    logger.info(f"  {i+1}. {title}")
                    logger.info(f"     URL: {url}")
                
                # 如果找到结果就停止测试
                logger.success(f"✅ {config_name} 配置工作正常!")
                return True
                
            else:
                logger.warning(f"未找到 '{query}' 的搜索结果")
                
        except Exception as e:
            logger.error(f"搜索 '{query}' 时出错: {e}")
    
    logger.warning(f"❌ {config_name} 未找到有效结果")
    return False


def analyze_search_issue():
    """分析搜索问题"""
    logger.info("\n=== 搜索问题分析 ===")
    
    possible_issues = [
        "1. 网站可能没有'进击的巨人'的搜索结果",
        "2. 搜索结果可能通过JavaScript动态加载",
        "3. 网站可能使用了不同的搜索机制",
        "4. 搜索页面可能显示的是默认内容而不是搜索结果",
        "5. 需要特定的搜索参数或格式"
    ]
    
    for issue in possible_issues:
        logger.info(issue)
    
    logger.info("\n建议的解决方案:")
    solutions = [
        "1. 尝试更常见的动漫名称进行搜索",
        "2. 检查网站是否有其他搜索方式",
        "3. 考虑直接分析动漫分类页面",
        "4. 使用浏览器开发者工具查看搜索的实际请求",
        "5. 尝试不同的搜索关键词格式"
    ]
    
    for solution in solutions:
        logger.info(solution)


def main():
    """主函数"""
    logger.info("🚀 girigirilove 优化配置测试")
    
    # 测试优化配置
    test_optimized_config()
    
    # 分析搜索问题
    analyze_search_issue()
    
    logger.info("\n" + "=" * 60)
    logger.success("优化配置测试完成!")
    logger.info("如果仍然没有找到搜索结果，建议:")
    logger.info("1. 手动验证网站确实有相关内容")
    logger.info("2. 尝试直接访问分类页面")
    logger.info("3. 考虑网站可能需要登录或有反爬虫保护")


if __name__ == "__main__":
    main()